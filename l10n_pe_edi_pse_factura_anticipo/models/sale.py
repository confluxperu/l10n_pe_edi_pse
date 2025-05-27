# -*- coding: utf-8 -*-

from odoo import models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        self.ensure_one()
        if self.is_downpayment:
            res['l10n_pe_edi_downpayment_line'] = True
            if len(self.invoice_lines)>0:
                invoice = self.invoice_lines.filtered(lambda i: i.move_id.state not in ('cancel'))
                res['l10n_pe_edi_downpayment_invoice_id'] = invoice[0].move_id.id
                if invoice[0].move_id.journal_id.l10n_latam_use_documents:
                    code_invoice = invoice[0].move_id.l10n_latam_document_type_id.code
                    l10n_pe_dte_advance_type = ''
                    if code_invoice=='01':
                        l10n_pe_dte_advance_type = '02'
                    elif code_invoice=='03':
                        l10n_pe_dte_advance_type = '03'
                    res['l10n_pe_edi_downpayment_ref_type'] = l10n_pe_dte_advance_type
                    res['l10n_pe_edi_downpayment_ref_number'] = invoice[0].move_id.name.replace(' ','')
                    if invoice[0].move_id.invoice_date:
                        res['l10n_pe_edi_downpayment_date'] = invoice[0].move_id.invoice_date
        return res