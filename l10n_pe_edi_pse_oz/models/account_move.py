# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
log = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

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

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _prepare_edi_vals_to_export(self):
        res = super()._prepare_edi_vals_to_export()
        if self.price_unit==0 and not self.l10n_pe_edi_affectation_reason in ('10','17','20','30','40'):
            res['price_subtotal_unit'] = self.product_id.bo_free_unit_price
            res['price_total_unit'] = self.product_id.bo_free_unit_price*1.18 if self.l10n_pe_edi_affectation_reason in ('11','12','13','14','15','16') else self.product_id.bo_free_unit_price
        return res