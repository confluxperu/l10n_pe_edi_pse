# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, _lt

import logging
log = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_get_edi_values_conflux(self, invoice):
        res = super(AccountEdiFormat, self)._l10n_pe_edi_get_edi_values_conflux(invoice)
        if invoice.l10n_pe_dte_dettran_origin_address_id:
            res["direccion_origen"]=(invoice.l10n_pe_dte_dettran_origin_address_id.street or '') \
                    + (invoice.l10n_pe_dte_dettran_origin_address_id.district_id and ', ' + invoice.l10n_pe_dte_dettran_origin_address_id.district_id.name or '') \
                    + (invoice.l10n_pe_dte_dettran_origin_address_id.province_id and ', ' + invoice.l10n_pe_dte_dettran_origin_address_id.province_id.name or '') \
                    + (invoice.l10n_pe_dte_dettran_origin_address_id.state_id and ', ' + invoice.l10n_pe_dte_dettran_origin_address_id.state_id.name or '') \
                    + (invoice.l10n_pe_dte_dettran_origin_address_id.country_id and ', ' + invoice.l10n_pe_dte_dettran_origin_address_id.country_id.name or '')
            res["ubigeo_origen"]=invoice.l10n_pe_dte_dettran_origin_address_id.district_id.code
        if invoice.l10n_pe_dte_dettran_delivery_address_id:
            res["direccion_destino"]=(invoice.l10n_pe_dte_dettran_delivery_address_id.street or '') \
                    + (invoice.l10n_pe_dte_dettran_delivery_address_id.district_id and ', ' + invoice.l10n_pe_dte_dettran_delivery_address_id.district_id.name or '') \
                    + (invoice.l10n_pe_dte_dettran_delivery_address_id.province_id and ', ' + invoice.l10n_pe_dte_dettran_delivery_address_id.province_id.name or '') \
                    + (invoice.l10n_pe_dte_dettran_delivery_address_id.state_id and ', ' + invoice.l10n_pe_dte_dettran_delivery_address_id.state_id.name or '') \
                    + (invoice.l10n_pe_dte_dettran_delivery_address_id.country_id and ', ' + invoice.l10n_pe_dte_dettran_delivery_address_id.country_id.name or '')
            res["ubigeo_destino"]=invoice.l10n_pe_dte_dettran_delivery_address_id.district_id.code

        if invoice.l10n_pe_dte_dettran_val_ref_serv_trans:
            res["val_ref_serv_trans"]=invoice.l10n_pe_dte_dettran_val_ref_serv_trans
        if invoice.l10n_pe_dte_dettran_val_ref_carga_efec:
            res["val_ref_carga_efec"]=invoice.l10n_pe_dte_dettran_val_ref_carga_efec
        if invoice.l10n_pe_dte_dettran_val_ref_carga_util:
            res["val_ref_carga_util"]=invoice.l10n_pe_dte_dettran_val_ref_carga_util
        if invoice.l10n_pe_dte_dettran_detalle_viaje:
            res["detalle_viaje"]=invoice.l10n_pe_dte_dettran_detalle_viaje
        return res