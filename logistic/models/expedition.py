# -*- encoding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang
import requests
import json
import datetime
import logging
log = logging.getLogger(__name__)


class LogisticDespatch(models.Model):
    _name = 'logistic.despatch'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Logistic Despatchs"
    _order = 'issue_date desc, name desc'
    _mail_post_access = 'read'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    type = fields.Selection([('out_despatch','Out Despatch'),('in_despatch','In Despatch')], string='Type', default='out_despatch')
    name = fields.Char(string='#', default='/', copy=False)
    ref = fields.Char(string='Reference')
    issue_date = fields.Date(string='Date despatch', copy=True)
    start_date = fields.Date(string='Date start', copy=True )
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('logistic.despatch'))
    partner_id = fields.Many2one('res.partner', string='Receiver')
    sequence_id = fields.Many2one('ir.sequence', string='Sequence')
    domain_sequence_id = fields.Many2many('ir.sequence', compute='_compute_domain_sequence_id')
    origin_address_id = fields.Many2one('res.partner', 'Origin Address')
    delivery_address_id = fields.Many2one('res.partner', 'Delivery Address', copy=True)
    driver_id = fields.Many2one('res.partner', string='Vehicle Driver', domain=[(
        'l10n_pe_edi_operator_license', '!=', False)], copy=True)
    carrier_id = fields.Many2one('res.partner', string='Carrier', domain=[(
        'l10n_pe_edi_mtc_number', '!=', False)], copy=True)

    total_volume = fields.Float(string='Volume', compute='_compute_weight_and_volume', store=True, copy=True)
    total_weight = fields.Float(string='Weight', compute='_compute_weight_and_volume', store=True, copy=True)
    weight_uom = fields.Many2one('uom.uom', string='UoM of weight', copy=True)
    packages = fields.Float(string='Packages', copy=True)
    note = fields.Text(string='Notes')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('cancel', 'Cancel')], string='Status', default='draft')
    line_ids = fields.One2many('logistic.despatch.line', 'despatch_id', copy=True)

    picking_ids = fields.Many2many('stock.picking', string='Pickings', copy=False)
    internal_number = fields.Char(string='Internal number', readonly=True, copy=False)
    despatch_origin = fields.Char(string='Origin', readonly=True, tracking=True,
        help="The document(s) that generated the despatch.")
    despatch_sent = fields.Boolean(readonly=True, default=False, copy=False,
        help="It indicates that the despatch has been sent.")
    despatch_user_id = fields.Many2one('res.users', copy=False, tracking=True,
        string='Salesperson',
        default=lambda self: self.env.user)
    user_id = fields.Many2one(string='User', related='despatch_user_id',
        help='Technical field used to fit the generic behavior in mail templates.')
    type_name = fields.Char('Type Name', compute='_compute_type_name')


    @api.model
    def default_get(self, fieldsx):
        res = super(LogisticDespatch, self).default_get(fieldsx)
        res.update({
            'issue_date': fields.Date.context_today(self)
        })

        return res

    @api.depends('warehouse_id')
    def _compute_domain_sequence_id(self):
        for rec in self:
            if rec.warehouse_id.despatch_sequence_ids:
                rec.domain_sequence_id = rec.warehouse_id.despatch_sequence_ids
            else:
                rec.domain_sequence_id = self.env['ir.sequence'].search([('code','=','logistic.despatch'),('company_id','=', rec.company_id.id)])

    @api.depends('line_ids.weight','line_ids.volume')
    def _compute_weight_and_volume(self):
        for rec in self:
            rec.total_weight = sum(self.line_ids.mapped('weight'))
            rec.total_volume = sum(self.line_ids.mapped('volume'))

    @api.depends('type')
    def _compute_type_name(self):
        type_name_mapping = {k: v for k, v in
                             self._fields['type']._description_selection(self.env)}
        replacements = {'out_despatch': _('Despatch')}

        for record in self:
            name = type_name_mapping[record.type]
            record.type_name = replacements.get(record.type, name)

    def unlink(self):
        for despatch in self:
            if despatch.state != 'draft':
                raise UserError(
                    'Despatch cannot be deleted if it is not in draft status.')
            if not (despatch.internal_number == None or despatch.internal_number == '' or despatch.internal_number == False):
                raise UserError(
                    'Despatch cannot be deleted!')
        return super().unlink()

    def action_cancel(self):
        for despatch in self:
            despatch.write({'state': 'cancel', 'name': False})

    def action_draft(self):
        for despatch in self:
            if despatch.state != 'cancel':
                raise UserError('The Despatch cannot be returned to draft if it is not in canceled status.')
            despatch.write({'state': 'draft'})

    def action_validate_despatch(self):
        pass

    def action_open(self):
        for rec in self:
            if not rec.sequence_id:
                raise UserError(_('Sequence is required to manage the despatch sequence'))
            rec.action_validate_despatch()
            if rec.internal_number and rec.internal_number != '':
                rec.name = rec.internal_number
            else:
                rec.name = rec.sequence_id.next_by_id()
                rec.internal_number = rec.name
            if not rec.issue_date:
                rec.issue_date = fields.Date.context_today(self)
            if not rec.start_date:
                rec.start_date = fields.Date.context_today(self)
            rec.state = 'open'

    def _get_despatch_display_name(self, show_ref=False):
        ''' Helper to get the display name of an despatch depending of its type.
        :param show_ref:    A flag indicating of the display name must include or not the despatch reference.
        :return:            A string representing the despatch.
        '''
        self.ensure_one()
        draft_name = ''
        if self.state == 'draft':
            draft_name += {
                'out_despatch': _('Draft Despatch'),
                'in_despatch': _('Draft Despatch'),
            }[self.type]
            if not self.name or self.name == '/':
                draft_name += ' (* %s)' % str(self.id)
            else:
                draft_name += ' ' + self.name
        return (draft_name or self.name) + (show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')

class LogisticDespatchLine(models.Model):
    _name = 'logistic.despatch.line'
    _description = 'Logistic Despatch Line'

    despatch_id = fields.Many2one('logistic.despatch', string='Despatch')
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    name = fields.Char(string='Description')
    uom_id = fields.Many2one(
        'uom.uom', string='UoM', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    weight = fields.Float(string='Weight', digits=(9,3))
    volume = fields.Float(string='Volume', digits=(9,3))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id
        self.name = self.product_id.display_name

    @api.onchange('product_id','quantity')
    def _onchange_prod_and_qty(self):
        if self.product_id:
            self.weight = self.product_id.weight*self.quantity
            self.volume = self.product_id.volume*self.quantity