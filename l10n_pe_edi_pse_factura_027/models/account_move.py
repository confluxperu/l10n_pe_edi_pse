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

    def _l10n_pe_edi_get_spot(self):
        res = super()._l10n_pe_edi_get_spot()
        if self.l10n_pe_edi_operation_type=='1004':
            if self.amount_total_signed<400:
                return {}
            else:
                amount_total = self.amount_total
                max_percent = res['payment_percent']
                if self.l10n_pe_dte_dettran_val_ref_serv_trans>amount_total:
                    if self.currency_id.name=='PEN':
                        amount_total = self.l10n_pe_dte_dettran_val_ref_serv_trans
                    else
                        amount_total = self.l10n_pe_dte_dettran_val_ref_serv_trans* (self.amount_total_signed/self.amount_total)

                amount_in_pen = self.currency_id._convert(
                    amount_total, pen_currency, self.company_id, self.invoice_date or fields.Date.today()
                )
                res['spot_amount'] = float_round(amount_total * (max_percent / 100.0), precision_rounding=1 if self.currency_id == pen_currency else self.currency_id.rounding)
                res['amount']: float_round(amount_in_pen * (max_percent / 100.0), precision_rounding=1)
        return res