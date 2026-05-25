# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, _lt

import logging
log = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_get_edi_values_conflux(self, invoice):
        res = super(AccountEdiFormat, self)._l10n_pe_edi_get_edi_values_conflux(invoice)
        invoice_sequence = invoice.nro_comp.replace(' ','').split('-')
        dte_serial = ''
        dte_number = ''
        if len(invoice_sequence)==2:
            dte_serial = invoice_sequence[0]
            dte_number = invoice_sequence[1]
        res['serie'] = dte_serial
        res['numero'] = dte_number
        if res['moneda']!='PEN':
            res['tipo_de_cambio'] = invoice.currency_rate
        if res['tipo_de_comprobante']=='07' or res['tipo_de_comprobante']=='08':
            if invoice.doc_invoice_relac:
                res['documento_que_se_modifica_tipo'] = invoice.doc_invoice_relac[0].type_document_id.code
                res['documento_que_se_modifica_numero'] = invoice.doc_invoice_relac[0].nro_comprobante
                if invoice.doc_invoice_relac[0].date:
                    res['documento_que_se_modifica_fecha'] = invoice.doc_invoice_relac[0].date.strftime('%Y-%m-%d')

        res["cliente_direccion"] = (invoice.partner_id.street or '') \
                                + (invoice.partner_id.district_id and ', ' + invoice.partner_id.district_id.name or '') \
                                + (invoice.partner_id.province_id and ', ' + invoice.partner_id.province_id.name or '') \
                                + (invoice.partner_id.state_id and ', ' + invoice.partner_id.state_id.name or '') \
                                + (invoice.partner_id.country_id and ', ' + invoice.partner_id.country_id.name or '')
        return res