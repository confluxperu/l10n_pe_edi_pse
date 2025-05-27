# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, _lt

import logging
log = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_get_edi_values_conflux(self, invoice):
        res = super(AccountEdiFormat, self)._l10n_pe_edi_get_edi_values_conflux(invoice)
        if res['moneda']!='PEN':
            res['tipo_de_cambio'] = invoice.currency_rate
        if res['tipo_de_comprobante']=='07' or res['tipo_de_comprobante']=='08':
            if invoice.doc_invoice_relac:
                res['documento_que_se_modifica_tipo'] = invoice.doc_invoice_relac[0].type_document_id.code
                res['documento_que_se_modifica_numero'] = invoice.doc_invoice_relac[0].nro_comprobante
                if invoice.doc_invoice_relac[0].date:
                    res['documento_que_se_modifica_fecha'] = invoice.doc_invoice_relac[0].date.strftime('%Y-%m-%d')
        return res