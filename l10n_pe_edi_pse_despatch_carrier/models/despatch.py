# -*- encoding: utf-8 -*-
from odoo import fields, api, models, _
import requests
import json
import datetime

import logging
log = logging.getLogger(__name__)


class LogisticDespatch(models.Model):
    _inherit = 'logistic.despatch'

    l10n_pe_edi_type = fields.Selection([('09', 'Remitente'),('31','Transportista')], string='Tipo de Guia', default='09')
    domain_sequence_id = fields.Many2many(compute='_compute_domain_sequence_id')
    l10n_pe_edi_receiver_id = fields.Many2one('res.partner', string='Destinatario')
    l10n_pe_edi_subcontractor_id = fields.Many2one('res.partner', string='Subcontratador')
    l10n_pe_edi_freight_payer_id = fields.Many2one('res.partner', string='Pagador de Flete - Tercero')
    l10n_pe_edi_vehicle_tuc = fields.Char(string='Vehiculo Principal - TUC', related='l10n_pe_edi_vehicle_1.l10n_pe_edi_vehicle_tuc', readonly=False)
    l10n_pe_edi_vehicle_2_tuc = fields.Char(string='Vehiculo Secundario 1 - TUC', related='l10n_pe_edi_vehicle_2.l10n_pe_edi_vehicle_tuc', readonly=False)
    l10n_pe_edi_vehicle_3_tuc = fields.Char(string='Vehiculo Secundario 2 - TUC', related='l10n_pe_edi_vehicle_3.l10n_pe_edi_vehicle_tuc', readonly=False)
    l10n_pe_edi_is_subcontracted_transport = fields.Boolean(string='Transporte Subcontratado')
    l10n_pe_edi_is_sender_freight_payer = fields.Boolean(string='Remitente Paga Flete')
    l10n_pe_edi_is_subcontractor_freight_payer = fields.Boolean(string='Subcontratado Paga Flete')
    l10n_pe_edi_is_third_party_freight_payer = fields.Boolean(string='Tercero Paga Flete')
    l10n_pe_edi_despatch_description = fields.Text(string='Descripcion de la Guia')

    @api.depends('warehouse_id')
    def _compute_domain_sequence_id(self):
        for rec in self:
            if rec.l10n_pe_edi_type == '31':
                if rec.warehouse_id.despatch_sequence_ids:
                    rec.domain_sequence_id = rec.warehouse_id.despatch_sequence_ids.filtered(lambda x: x.code == 'logistic.despatch31')
                else:
                    rec.domain_sequence_id = self.env['ir.sequence'].search([('code','=','logistic.despatch31'),('company_id','=', rec.company_id.id)])
            else:
                if rec.warehouse_id.despatch_sequence_ids:
                    rec.domain_sequence_id = rec.warehouse_id.despatch_sequence_ids
                else:
                    rec.domain_sequence_id = self.env['ir.sequence'].search([('code','=','logistic.despatch'),('company_id','=', rec.company_id.id)])

    def _l10n_pe_prepare_dte(self):
        res = super(LogisticDespatch, self)._l10n_pe_prepare_dte()
        res['tipo_de_guia'] = self.l10n_pe_edi_type or '31'
        if res['tipo_de_guia']=='31':
            #if self.l10n_pe_edi_despatch_description!= None and self.l10n_pe_edi_despatch_description!= "":
            res['detalle_de_bienes_a_transportar'] = self.l10n_pe_edi_despatch_description or ""
            res['tuc_vehiculo_principal'] = self.l10n_pe_edi_vehicle_tuc
            if self.l10n_pe_edi_vehicle_2:
                res['placa_de_vehiculo_secundario_1_tuc'] = self.l10n_pe_edi_vehicle_2_tuc
            if self.l10n_pe_edi_vehicle_3:
                res['placa_de_vehiculo_secundario_2_tuc'] = self.l10n_pe_edi_vehicle_3_tuc

            res['transporte_subcontratado'] = self.l10n_pe_edi_is_subcontracted_transport
            res['pagador_de_flete_remitente'] = self.l10n_pe_edi_is_sender_freight_payer
            res['pagador_de_flete_subcontratador'] = self.l10n_pe_edi_is_subcontractor_freight_payer
            res['pagador_de_flete_tercero'] = self.l10n_pe_edi_is_third_party_freight_payer
            
            if self.l10n_pe_edi_is_third_party_freight_payer and self.l10n_pe_edi_freight_payer_id:
                res['pagador_flete_denominacion'] = self.l10n_pe_edi_freight_payer_id.name
                res['pagador_flete_numero_de_documento'] = self.l10n_pe_edi_freight_payer_id.vat
                res['pagador_flete_tipo_de_documento'] = self.l10n_pe_edi_freight_payer_id.l10n_latam_identification_type_id.l10n_pe_vat_code

            if self.l10n_pe_edi_subcontractor_id:
                res['subcontratador_denominacion'] = self.l10n_pe_edi_subcontractor_id.name
                res['subcontratador_numero_de_documento'] = self.l10n_pe_edi_subcontractor_id.vat
                res['subcontratador_tipo_de_documento'] = self.l10n_pe_edi_subcontractor_id.l10n_latam_identification_type_id.l10n_pe_vat_code

            if self.l10n_pe_edi_receiver_id:
                res['destinatario_denominacion'] = self.l10n_pe_edi_receiver_id.name
                res['destinatario_numero_de_documento'] = self.l10n_pe_edi_receiver_id.vat
                res['destinatario_tipo_de_documento'] = self.l10n_pe_edi_receiver_id.l10n_latam_identification_type_id.l10n_pe_vat_code
        return res