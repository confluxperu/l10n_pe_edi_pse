# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round

import logging
log = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_pe_edi_pse_uid = fields.Char(string='PSE Unique identifier', copy=False)
    l10n_pe_edi_pse_cancel_uid = fields.Char(string='PSE Identifier for Cancellation', copy=False)
    l10n_pe_edi_pse_attachment_ids = fields.Many2many('ir.attachment', string='EDI Attachments')
    l10n_pe_edi_pse_status = fields.Selection([
        ('ask_for_status', 'Ask For Status'),
        ('accepted', 'Accepted'),
        ('objected', 'Accepted With Objections'),
        ('rejected', 'Rejected'),
    ], string='SUNAT DTE status', copy=False, tracking=True, help="""Status of sending the DTE to the SUNAT:
    - Ask For Status: The DTE is asking for its status to the SUNAT.
    - Accepted: The DTE has been accepted by SUNAT.
    - Accepted With Objections: The DTE has been accepted with objections by SUNAT.
    - Rejected: The DTE has been rejected by SUNAT.""")
    l10n_pe_edi_pse_void_status = fields.Selection([
        ('ask_for_status', 'Ask For Status'),
        ('accepted', 'Accepted'),
        ('objected', 'Accepted With Objections'),
        ('rejected', 'Rejected'),
    ], string='SUNAT DTE Void status', copy=False, tracking=True, help="""Status of sending the DTE to the SUNAT:
    - Ask For Status: The DTE is asking for its status to the SUNAT.
    - Accepted: The DTE has been accepted by SUNAT.
    - Accepted With Objections: The DTE has been accepted with objections by SUNAT.
    - Rejected: The DTE has been rejected by SUNAT.""")
    l10n_pe_edi_accepted_by_sunat = fields.Boolean(string='EDI Accepted by Sunat', copy=False)
    l10n_pe_edi_void_accepted_by_sunat = fields.Boolean(string='Void EDI Accepted by Sunat', copy=False)
    l10n_pe_edi_rectification_ref_type = fields.Many2one('l10n_latam.document.type', string='Rectification - Invoice Type')
    l10n_pe_edi_rectification_ref_number = fields.Char('Rectification - Invoice number')
    l10n_pe_edi_rectification_ref_date = fields.Date('Rectification - Invoice Date')
    l10n_pe_edi_payment_fee_ids = fields.One2many('account.move.l10n_pe_payment_fee','move_id', string='Credit Payment Fees')
    l10n_pe_edi_transportref_ids = fields.One2many(
        'account.move.l10n_pe_transportref', 'move_id', string='Attached Despatchs', copy=True)
    
    l10n_pe_edi_hash = fields.Char(string='DTE Hash', copy=False)
    l10n_pe_edi_xml_file = fields.Many2one('ir.attachment', string='DTE file', copy=False)
    l10n_pe_edi_xml_file_link = fields.Char(string='DTE file', compute='_compute_l10n_pe_edi_links')
    l10n_pe_edi_pdf_file = fields.Many2one('ir.attachment', string='DTE PDF file', copy=False)
    l10n_pe_edi_pdf_file_link = fields.Char(string='DTE PDF file', compute='_compute_l10n_pe_edi_links')
    l10n_pe_edi_cdr_file = fields.Many2one('ir.attachment', string='CDR file', copy=False)
    l10n_pe_edi_cdr_file_link = fields.Char(string='CDR file', compute='_compute_l10n_pe_edi_links')
    l10n_pe_edi_cdr_void_file = fields.Many2one('ir.attachment', string='CDR Void file', copy=False)
    l10n_pe_edi_cdr_void_file_link = fields.Char(string='CDR Void file', compute='_compute_l10n_pe_edi_links')
    l10n_pe_edi_show_cancel_button = fields.Boolean(compute='_compute_edi_show_cancel_button2')
    l10n_pe_edi_show_reset_to_draft_button = fields.Boolean(compute='_compute_edi_show_reset_to_draft_button')

    def _compute_l10n_pe_edi_links(self):
        for move in self:
            move.l10n_pe_edi_xml_file_link = move.l10n_pe_edi_xml_file.url if move.l10n_pe_edi_xml_file else None
            move.l10n_pe_edi_pdf_file_link = move.l10n_pe_edi_pdf_file.url if move.l10n_pe_edi_pdf_file else None
            move.l10n_pe_edi_cdr_file_link = move.l10n_pe_edi_cdr_file.url if move.l10n_pe_edi_cdr_file else None
            move.l10n_pe_edi_cdr_void_file_link = move.l10n_pe_edi_cdr_void_file.url if move.l10n_pe_edi_cdr_void_file else None

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft=soft)
        pe_edi_format = self.env.ref('l10n_pe_edi_pse_factura.edi_pe_pse')
        for move in self.filtered(lambda m: m.l10n_pe_edi_is_required):
            move.l10n_pe_edi_compute_fees()
            self.env.ref('account_edi.ir_cron_edi_network')._trigger()
        return res
    
    def _get_starting_sequence(self):
        # OVERRIDE
        if self.l10n_pe_edi_is_required and self.l10n_latam_document_type_id:
            doc_mapping = {'01': 'FFI', '03': 'BOL', '07': 'CNE', '08': 'NDI'}
            middle_code = doc_mapping.get(self.l10n_latam_document_type_id.code, self.journal_id.code)
            # TODO: maybe there is a better method for finding decent 2nd journal default invoice names
            if self.journal_id.code != 'INV':
                middle_code = self.journal_id.code[:3]
            return "%s %s-00000000" % (self.l10n_latam_document_type_id.doc_code_prefix, middle_code)

        return super()._get_starting_sequence()

    def _l10n_pe_edi_get_retention(self):
        self.ensure_one()
        percent = 3 if self.partner_id.l10n_pe_edi_retention_type=='01' else 6
        if not self.partner_id.l10n_pe_edi_retention_type or self.move_type == 'out_refund':
            return {}
        
        if self.amount_total_signed<700:
            return {}

        return {
            'retention_type': self.partner_id.l10n_pe_edi_retention_type,
            'retention_base': self.amount_total,
            'base_amount': self.amount_total_signed,
            'retention_amount': float_round(self.amount_total * (percent / 100.0), precision_rounding=0.01),
            'amount': float_round(self.amount_total_signed * (percent / 100.0), precision_rounding=1),
        }
    
    def _l10n_pe_edi_get_spot(self):
        res = super()._l10n_pe_edi_get_spot()
        if self.amount_total_signed<700:
            return {}
        return res

    def l10n_pe_edi_compute_fees(self):
        self.l10n_pe_edi_payment_fee_ids.unlink()
        spot = self._l10n_pe_edi_get_spot()
        spot_amount = 0
        if spot:
            spot_amount = spot['amount'] if self.currency_id == self.company_id.currency_id else spot['spot_amount']
        retention = self._l10n_pe_edi_get_retention()
        retention_amount = 0
        if retention:
            retention_amount = retention['amount'] if self.currency_id == self.company_id.currency_id else retention['retention_amount']
        free_amount = 0
        for subtotal in self.tax_totals['groups_by_subtotal']['Subtotal']:
            if subtotal['tax_group_name']=='GRA':
                free_amount+=subtotal['tax_group_amount']+subtotal['tax_group_base_amount']
        invoice_date_due_vals_list = []
        deduction = spot_amount + retention_amount + free_amount
        sign = 1 if self.is_inbound(include_receipts=True) else -1
        tax_amount_currency = self.amount_tax * sign
        tax_amount = self.amount_tax
        untaxed_amount_currency = self.amount_untaxed * sign - deduction
        untaxed_amount = self.amount_untaxed - deduction

        if untaxed_amount>0 and self.move_type == 'out_invoice':
            if self.invoice_payment_term_id:
                invoice_payment_terms = self.invoice_payment_term_id._compute_terms(
                    date_ref=self.invoice_date or self.date or fields.Date.context_today(self),
                    currency=self.currency_id,
                    tax_amount_currency=tax_amount_currency,
                    tax_amount=tax_amount,
                    untaxed_amount_currency=untaxed_amount_currency,
                    untaxed_amount=untaxed_amount,
                    company=self.company_id,
                    cash_rounding=self.invoice_cash_rounding_id,
                    sign=sign
                )
                for term_line in invoice_payment_terms['line_ids']:
                    due_date = fields.Date.to_date(term_line.get('date'))
                    if due_date > self.invoice_date:
                        invoice_date_due_vals_list.append([0, 0, {
                            'amount_total': term_line['company_amount'],
                            'currency_id': self.currency_id.id,
                            'date_due': due_date
                        }])
            else:
                if self.invoice_date_due and self.invoice_date_due > self.invoice_date:
                    invoice_date_due_vals_list.append([0, 0, {
                        'amount_total': self.amount_total_signed,
                        'currency_id': self.currency_id.id,
                        'date_due': self.invoice_date_due
                    }])

            self.write({
                'l10n_pe_edi_payment_fee_ids': invoice_date_due_vals_list
            })

    def _retry_edi_documents_error_hook(self):
        for move in self.filtered(lambda m: m.l10n_pe_edi_pse_uid and (m.l10n_pe_edi_pse_status=='ask_for_status')):
            move.edi_document_ids.filtered(lambda d: d.state in ('sent')).write({'state': 'to_send'})
        for move in self.filtered(lambda m: m.l10n_pe_edi_pse_cancel_uid and (m.l10n_pe_edi_pse_void_status=='ask_for_status')):
            move.edi_document_ids.filtered(lambda d: d.state in ('cancelled')).write({'state': 'to_cancel'})
    
    def _l10n_pe_edi_get_extra_report_values(self):
        self.ensure_one()
        if not self.l10n_pe_edi_pse_uid:
            res = super()._l10n_pe_edi_get_extra_report_values()
            return res

        serie_folio = self._l10n_pe_edi_get_serie_folio()
        qr_code_values = [
            self.company_id.vat,
            self.company_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            serie_folio['serie'],
            serie_folio['folio'],
            str(self.amount_tax),
            str(self.amount_total),
            fields.Date.to_string(self.date),
            self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            self.commercial_partner_id.vat or '00000000',
            ''
        ]

        return {
            'qr_str': '|'.join(qr_code_values) + '|\r\n',
            'amount_to_text': self._l10n_pe_edi_amount_to_text(),
        }
    
    @api.depends('edi_document_ids.state')
    def _compute_edi_show_cancel_button(self):
        for move in self:
            move.edi_show_cancel_button = False
    
    @api.depends('edi_document_ids.state')
    def _compute_edi_show_cancel_button2(self):
        for move in self:
            is_conflux_provider = False
            edi_show_cancel_button = False
            if move.state != 'posted':
                move.l10n_pe_edi_show_cancel_button = False
                continue
            for doc in move.edi_document_ids.filtered(lambda doc: doc.state == 'sent'):
                move_applicability = doc.edi_format_id._get_move_applicability(move)
                if doc.edi_format_id==self.env.ref('l10n_pe_edi_pse_factura.edi_pe_pse'):
                    move.l10n_pe_edi_show_cancel_button = True
                    is_conflux_provider = True
                    break
                if move_applicability and move_applicability.get('cancel'):
                    edi_show_cancel_button = True
            if not is_conflux_provider:
                move.l10n_pe_edi_show_cancel_button = edi_show_cancel_button

    @api.depends('restrict_mode_hash_table', 'state')
    def _compute_edi_show_reset_to_draft_button(self):
        for move in self:
            move.l10n_pe_edi_show_reset_to_draft_button = (
                not move.restrict_mode_hash_table \
                and (move.state == 'cancel' or (move.state == 'posted' and not move.need_cancel_request))
            )
        
    def _can_force_cancel(self):
        self.ensure_one()
        pe_edi_format = self.env.ref('l10n_pe_edi_pse_factura.edi_pe_pse')
        if pe_edi_format._get_move_applicability(self):
            return True
        return super()._can_force_cancel()

    def button_cancel(self):
        pe_edi_format = self.env.ref('l10n_pe_edi_pse_factura.edi_pe_pse')
        if self.is_sale_document() and self.l10n_pe_edi_pse_uid and not self.l10n_pe_edi_pse_cancel_uid:
            cancel_reason = self.l10n_pe_edi_cancel_reason or 'Anulacion'
            self.write({'l10n_pe_edi_cancel_reason':cancel_reason})
            self.edi_document_ids.filtered(lambda doc: doc.state == 'to_send').write({'state': 'sent', 'error': False, 'blocking_level': False})
        res = super().button_cancel()
        return res

    def button_cancel_posted_moves(self):
        # OVERRIDE
        pe_edi_format = self.env.ref('l10n_pe_edi_pse_factura.edi_pe_pse')
        pe_invoices = self.filtered(pe_edi_format._get_move_applicability)
        if pe_invoices:
            cancel_reason_needed = pe_invoices.filtered(lambda move: not move.l10n_pe_edi_cancel_reason)
            if cancel_reason_needed:
                return self.env.ref('l10n_pe_edi.action_l10n_pe_edi_cancel').sudo().read()[0]
        return super().button_cancel_posted_moves()
    
    def action_l10n_pe_edi_pse_status(self):
        for rec in self:
            if rec.l10n_pe_edi_pse_status=='ask_for_status' and rec.l10n_pe_edi_pse_uid:
                docs = rec.edi_document_ids.filtered(lambda d: d.state in ('sent',))
                edi_filename = '%s-%s-%s' % (
                    rec.company_id.vat,
                    rec.l10n_latam_document_type_id.code,
                    rec.name.replace(' ', ''),
                )
                docs.edi_format_id._l10n_pe_edi_sign_invoices_conflux(rec, edi_filename, '')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_pe_edi_allowance_charge_reason_code = fields.Selection(selection_add=[('03','Descuentos globales que no afectan la base imponible del IGV/IVAP'),('40', 'Anticipo de ISC')])
    l10n_pe_edi_downpayment_line = fields.Boolean('Is Downpayment?', store=True, default=False)
    l10n_pe_edi_downpayment_invoice_id = fields.Many2one('account.move', string='Downpayment Invoice', store=True, readonly=True, help='Invoices related to the advance regualization')
    l10n_pe_edi_downpayment_ref_type = fields.Selection([('02','Factura'),('03','Boleta de venta')], string='Downpayment Ref. Type')
    l10n_pe_edi_downpayment_ref_number = fields.Char('Downpayment Ref. Number')
    l10n_pe_edi_downpayment_date = fields.Date('Downpayment date')

    def _prepare_edi_vals_to_export(self):
        res = super()._prepare_edi_vals_to_export()
        res.update({
            'price_subtotal_unit': self.price_subtotal / self.quantity if self.quantity else 0.0,
            'price_total_unit': self.price_total / self.quantity if self.quantity else 0.0,
        })
        return res
    
    def show_detail_downpayment(self):
        view = self.env.ref('l10n_pe_edi_pse_factura.detail_downpayment', False)
        return {
            'name': self.name ,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
            ),
        }