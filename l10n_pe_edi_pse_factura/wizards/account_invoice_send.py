# -*- coding: utf-8 -*-
import base64

import requests

from odoo import api, models
import logging
log = logging.getLogger(__name__)

class AccountInvoiceSend(models.TransientModel):
    _inherit = "account.move.send"
    
    def _print_document(self):
        """ to override for each type of models that will use this composer."""        
        """self.ensure_one()
        action = self.invoice_ids.action_invoice_print()
        action.update({'close_on_report_download': True})
        return action"""
        return {'type': 'ir.actions.act_window_close'}
    
    @api.model
    def _get_invoice_extra_attachments_data(self, move):
        invoice_id = move
        res = super(AccountInvoiceSend, self)._get_invoice_extra_attachments_data(move)
        if move.company_id.l10n_pe_edi_provider!='conflux':
            return res
        conf = self.env['ir.config_parameter']
        pdf_format_pse = conf.sudo().get_param('account.l10n_pe_edi_pdf_use_pse_%s' % invoice_id.company_id.id,"False")
        
        if pdf_format_pse.lower() == "true":
            pdf_format_pse = True
        else:
            pdf_format_pse = False
        if invoice_id.l10n_pe_edi_pdf_file and pdf_format_pse:
            r = requests.get(invoice_id.l10n_pe_edi_pdf_file.url)
            data_content = r.content
            invoice_id.l10n_pe_edi_pdf_file.write({
                "datas": base64.encodebytes(data_content),
                "type": "binary",
            })
            res = []
            res.append({
                'id': invoice_id.l10n_pe_edi_pdf_file.id,
                'name': invoice_id.l10n_pe_edi_pdf_file.name,
                'mimetype': invoice_id.l10n_pe_edi_pdf_file.mimetype,
                'placeholder': False,
                'protect_from_deletion': True,
            })
        if invoice_id.l10n_pe_edi_cdr_file:
            r = requests.get(invoice_id.l10n_pe_edi_pdf_file.url)
            data_content = r.content
            invoice_id.l10n_pe_edi_cdr_file.write({
                "datas": base64.encodebytes(data_content),
                "type": "binary",
            })
            res.append({
                'id': invoice_id.l10n_pe_edi_cdr_file.id,
                'name': invoice_id.l10n_pe_edi_cdr_file.name,
                'mimetype': invoice_id.l10n_pe_edi_cdr_file.mimetype,
                'placeholder': False,
                'protect_from_deletion': True,
            })
        if invoice_id.l10n_pe_edi_xml_file:
            r = requests.get(invoice_id.l10n_pe_edi_xml_file.url)
            data_content = r.content
            invoice_id.l10n_pe_edi_xml_file.write({
                "datas": base64.encodebytes(data_content),
                "type": "binary",
            })
            res.append({
                'id': invoice_id.l10n_pe_edi_xml_file.id,
                'name': invoice_id.l10n_pe_edi_xml_file.name,
                'mimetype': invoice_id.l10n_pe_edi_xml_file.mimetype,
                'placeholder': False,
                'protect_from_deletion': True,
            })
        return res
