# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
import logging
log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    l10n_pe_dte_dettran_origin_address_id = fields.Many2one('res.partner', string='Dirección de origen')
    l10n_pe_dte_dettran_delivery_address_id = fields.Many2one('res.partner', string='Dirección de llegada')
    l10n_pe_dte_dettran_val_ref_serv_trans = fields.Float('Valor Referencial', digits=(9,2))
    l10n_pe_dte_dettran_val_ref_carga_efec = fields.Float('Carga Efectiva (TM)', digits=(9,3))
    l10n_pe_dte_dettran_val_ref_carga_util = fields.Float('Carga Util (TM)', digits=(9,3))
    l10n_pe_dte_dettran_detalle_viaje = fields.Char('Detalle de Viaje')