# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import json
import logging
import requests
log = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.retention.comp"

    l10n_pe_dte_status = fields.Selection([
        ('not_sent', 'Pending To Be Sent'),
        ('ask_for_status', 'Ask For Status'),
        ('accepted', 'Accepted'),
        ('objected', 'Accepted With Objections'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('manual', 'Manual'),
    ], default='not_sent', string='SUNAT DTE status', copy=False, tracking=True, help="""Status of sending the DTE to the SUNAT:
    - Not sent: the DTE has not been sent to SUNAT but it has created.
    - Ask For Status: The DTE is asking for its status to the SUNAT.
    - Accepted: The DTE has been accepted by SUNAT.
    - Accepted With Objections: The DTE has been accepted with objections by SUNAT.
    - Rejected: The DTE has been rejected by SUNAT.
    - Manual: The DTE is sent manually, i.e.: the DTE will not be sending manually.""")
    l10n_pe_dte_status_response = fields.Char(string='SUNAT DTE status response', copy=False)
    l10n_pe_dte_void_status = fields.Selection([
        ('not_sent', 'Pending To Be Sent'),
        ('ask_for_status', 'Ask For Status'),
        ('accepted', 'Accepted'),
        ('objected', 'Accepted With Objections'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('manual', 'Manual'),
    ], string='SUNAT DTE Void status', copy=False, tracking=True, help="""Status of sending the Void DTE to the SUNAT:
    - Not sent: the DTE has not been sent to SUNAT but it has created.
    - Ask For Status: The DTE is asking for its status to the SUNAT.
    - Accepted: The DTE has been accepted by SUNAT.
    - Accepted With Objections: The DTE has been accepted with objections by SUNAT.
    - Rejected: The DTE has been rejected by SUNAT.
    - Manual: The DTE is sent manually, i.e.: the DTE will not be sending manually.""")
    l10n_pe_dte_void_status_response = fields.Char(string='SUNAT DTE Void status response', copy=False)
    l10n_pe_dte_cancel_reason = fields.Char(
        string="Cancel Reason", copy=False,
        help="Reason given by the user to cancel this move")
    l10n_pe_dte_partner_status = fields.Selection([
        ('not_sent', 'Not Sent'),
        ('sent', 'Sent'),
    ], string='Partner DTE status', copy=False, help="""
    Status of sending the DTE to the partner:
    - Not sent: the DTE has not been sent to the partner but it has sent to SUNAT.
    - Sent: The DTE has been sent to the partner.""")
    l10n_pe_dte_file = fields.Many2one('ir.attachment', string='DTE file', copy=False)
    l10n_pe_dte_file_link = fields.Char(string='DTE file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_hash = fields.Char(string='DTE Hash', copy=False)
    l10n_pe_cdr_file = fields.Many2one('ir.attachment', string='CDR file', copy=False)
    l10n_pe_cdr_void_file = fields.Many2one('ir.attachment', string='CDR Void file', copy=False)
    l10n_pe_dte_pdf_file = fields.Many2one('ir.attachment', string='DTE PDF file', copy=False)
    l10n_pe_dte_pdf_file_link = fields.Char(string='DTE PDF file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_cdr_file = fields.Many2one('ir.attachment', string='CDR file', copy=False)
    l10n_pe_dte_cdr_file_link = fields.Char(string='CDR file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_cdr_void_file = fields.Many2one('ir.attachment', string='CDR Void file', copy=False)
    l10n_pe_dte_cdr_void_file_link = fields.Char(string='CDR Void file', compute='_compute_l10n_pe_dte_void_links')
    l10n_pe_dte_void_file = fields.Many2one('ir.attachment', string='XML Void file', copy=False)
    l10n_pe_dte_void_file_link = fields.Char(string='XML Void file', compute='_compute_l10n_pe_dte_void_links')
    l10n_pe_dte_void_pdf_file = fields.Many2one('ir.attachment', string='PDF Void file', copy=False)
    l10n_pe_dte_void_pdf_file_link = fields.Char(string='PDF Void file', compute='_compute_l10n_pe_dte_void_links')
    l10n_pe_dte_void_cdr_file = fields.Many2one('ir.attachment', string='CDR Void file', copy=False)
    l10n_pe_dte_void_cdr_file_link = fields.Char(string='CDR Void file', compute='_compute_l10n_pe_dte_void_links')
    l10n_pe_dte_withholding_type = fields.Selection([
        ('01', 'Tasa 3%'),
        ('02', 'Tasa 6%'),
    ], string='IGV Retention Type', default='01', copy=True, readonly=True,
        states={'draft': [('readonly', False)]},)
    l10n_pe_dte_conflux_uid = fields.Char(string='DTE Conflux UID', copy=False)
    l10n_pe_dte_conflux_void_uid = fields.Char(string='DTE Void Conflux UID', copy=False)

    def _compute_l10n_pe_dte_links(self):
        for move in self:
            move.l10n_pe_dte_file_link = move.l10n_pe_dte_file.url if move.l10n_pe_dte_file else None
            move.l10n_pe_dte_pdf_file_link = move.l10n_pe_dte_pdf_file.url if move.l10n_pe_dte_pdf_file else None
            move.l10n_pe_dte_cdr_file_link = move.l10n_pe_dte_cdr_file.url if move.l10n_pe_dte_cdr_file else None

    def _compute_l10n_pe_dte_void_links(self):
        for move in self:
            move.l10n_pe_dte_void_file_link = move.l10n_pe_dte_void_file.url if move.l10n_pe_dte_void_file else None
            move.l10n_pe_dte_void_pdf_file_link = move.l10n_pe_dte_void_pdf_file.url if move.l10n_pe_dte_void_pdf_file else None
            move.l10n_pe_dte_void_cdr_file_link = move.l10n_pe_dte_void_cdr_file.url if move.l10n_pe_dte_void_cdr_file else None
            move.l10n_pe_dte_cdr_void_file_link = move.l10n_pe_dte_cdr_void_file.url if move.l10n_pe_dte_cdr_void_file else None

    def l10n_pe_dte_action_summary_void(self):
        view = self.env.ref('l10n_pe_edi_itgrupo_withholding.view_account_retention_comp_void_form', False)
        return {
            'name': self.name ,
            'type': 'ir.actions.act_window',
            'view_mode': 'form', 
            'res_model': 'account.perception',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    def l10n_pe_dte_action_check(self):
        
        ir_attach = self.env['ir.attachment']
        for move in self.filtered(
                lambda x: x.company_id.country_id.code == "PE" and
                            x.company_id.l10n_pe_edi_provider in ['conflux']):
            if move.l10n_pe_dte_conflux_uid:
                if move.l10n_pe_dte_status in ('ask_for_status','rejected') or move.l10n_pe_dte_void_status=='ask_for_status':
                    log.info(move.company_id.l10n_pe_edi_pse_secret_key)
                    log.info('https://einvoice.conflux.pe/api/v/1/account_einvoice/retention/%s/status/' % move.l10n_pe_dte_conflux_uid)
                    data_dict = {}
                    response = self._send_json_to_conflux(token=move.company_id.l10n_pe_edi_pse_secret_key, method="get", data_dict=data_dict, ws_url='https://einvoice.conflux.pe/api/v/1/account_einvoice/retention/%s/status/' % move.l10n_pe_dte_conflux_uid)
                    if response[0]:
                        log.info(response[1])
                        if response[1].get("estado")=="open":
                            _invoice = {
                                "l10n_pe_dte_status": 'ask_for_status',
                            }
                            if response[1].get("emision_aceptada")==True:
                                _invoice.update({
                                    "l10n_pe_dte_status": 'accepted',
                                    })
                                has_sunat_notes = False
                                if response[1].get('sunat_note', False) and response[1].get('sunat_note', False)!="":
                                    has_sunat_notes = True
                                    _invoice.update({
                                        "l10n_pe_dte_status": 'objected',
                                    })

                                if response[1].get("enlace_del_cdr"):
                                    xml_attach = ir_attach.create({
                                        "name":"R-%s-%s-%s.xml" % (move.company_id.vat, '20', response[1].get('nombre')),
                                        'res_model': self._name,
                                        'res_id': self.id,
                                        "type":'url',
                                        "url":response[1].get("enlace_del_cdr")
                                    })
                                    _invoice.update({
                                        "l10n_pe_dte_cdr_file":xml_attach.id,
                                        "l10n_pe_dte_status_response": '%s - %s' % (response[1].get('sunat_description', ''), response[1].get('sunat_note', '')) if has_sunat_notes else '',
                                    })
                            elif response[1].get("emision_rechazada")==True:
                                _invoice.update({
                                    "l10n_pe_dte_status": 'rejected',
                                    "l10n_pe_dte_status_response": '%s - %s' % (response[1].get('sunat_description', ''), response[1].get('sunat_note', ''))
                                })
                            move.write(_invoice)
                        elif response[1].get("estado")=="annulled":
                            _invoice = {
                                "l10n_pe_dte_void_status": 'ask_for_status',
                            }
                            response_void = self._send_json_to_conflux(token=move.company_id.l10n_pe_edi_pse_secret_key, method="get", data_dict=data_dict, ws_url='https://einvoice.conflux.pe/api/v/1/einvoice_void/void_rr/%s/status/' % move.l10n_pe_dte_conflux_void_uid)
                            if response[1].get("baja_aceptada")==True:
                                _invoice.update({
                                    "l10n_pe_dte_void_status": 'accepted',
                                    })
                                xml_void_attach = ir_attach.create({
                                    "name":"%s-%s.xml" % (move.company_id.vat, move.id),
                                    'res_model': self._name,
                                    'res_id': self.id,
                                    "type":'url',
                                    "url":response_void[1].get("enlace_del_xml")
                                })
                                pdf_void_attach = ir_attach.create({
                                    "name":"%s-%s.pdf" % (move.company_id.vat, move.id),
                                    'res_model': self._name,
                                    'res_id': self.id,
                                    "type":'url',
                                    "url":response_void[1].get("enlace_del_pdf")
                                })
                                cdr_void_attach = ir_attach.create({
                                    "name":"R-%s-%s.xml" % (move.company_id.vat, move.id),
                                    'res_model': self._name,
                                    'res_id': self.id,
                                    "type":'url',
                                    "url":response_void[1].get("enlace_del_cdr")
                                })
                                _invoice.update({
                                    "l10n_pe_dte_void_file":xml_void_attach.id,
                                    "l10n_pe_dte_void_pdf_file":pdf_void_attach.id,
                                    "l10n_pe_dte_void_cdr_file":cdr_void_attach.id,
                                    "l10n_pe_dte_void_status_response": '%s - %s' % (response_void[1].get('sunat_responsecode', ''), response_void[1].get('sunat_description', '')),
                                })
                            elif response[1].get("baja_rechazada")==True:
                                _invoice.update({
                                    "l10n_pe_dte_void_status": 'rejected',
                                    "l10n_pe_dte_void_status_response": '%s - %s' % (response_void[1].get('sunat_responsecode', ''), response_void[1].get('sunat_description', ''))
                                })
                            move.write(_invoice)
                    else:
                        raise UserError(response[1])

    def l10n_pe_dte_action_send(self):
        ir_attach = self.env['ir.attachment']
        for move in self.filtered(
                lambda x: x.company_id.country_id.code == "PE" and
                            x.company_id.l10n_pe_edi_provider in ['conflux']):
            if not move.l10n_pe_dte_conflux_uid:
                data_dict = move._l10n_pe_prepare_dte_withholding_conflux()
                log.info(data_dict)
                response = self._send_json_to_conflux(ws_url='https://einvoice.conflux.pe/api/v/1/account_einvoice/retention/',token=move.company_id.l10n_pe_edi_pse_secret_key, data_dict=data_dict)
                if response[0]:
                    if response[1].get("status")=="success":
                        xml_attach = ir_attach.create({
                            "name":"%s.xml" % data_dict.get('nombre_de_archivo'),
                            'res_model': self._name,
                            'res_id': move.id,
                            "type":'url',
                            "url":response[1]["success"]["data"].get("enlace_del_xml")
                        })
                        pdf_attach = ir_attach.create({
                            "name":"%s.pdf" % data_dict.get('nombre_de_archivo'),
                            'res_model': self._name,
                            'res_id': move.id,
                            "type":'url',
                            "url":response[1]["success"]["data"].get("enlace_del_pdf")
                        })

                        _invoice = {
                            "l10n_pe_dte_file":xml_attach.id,
                            "l10n_pe_dte_pdf_file":pdf_attach.id,
                            "l10n_pe_dte_hash":response[1]["success"]["data"].get("codigo_hash"),
                            "l10n_pe_dte_status":'ask_for_status',
                            "l10n_pe_dte_partner_status":'not_sent',
                            "l10n_pe_dte_conflux_uid": response[1]["success"]["data"].get("uid"),
                        }

                        has_sunat_notes = False
                        if response[1]["success"]["data"].get('sunat_note', False) and response[1]["success"]["data"].get('sunat_note', False)!="":
                            has_sunat_notes = True
                            _invoice.update({
                                "l10n_pe_dte_status": 'objected',
                            })

                        if response[1]["success"]["data"].get("enlace_del_cdr") and response[1]["success"]["data"].get("emision_aceptada", False):
                            cdr_attach = ir_attach.create({
                                "name":"R-%s.xml" % data_dict.get('nombre_de_archivo'),
                                'res_model': self._name,
                                'res_id': move.id,
                                "type":'url',
                                "url":response[1]["success"]["data"].get("enlace_del_cdr")
                            })
                            _invoice.update({
                                "l10n_pe_dte_cdr_file":cdr_attach.id,
                                "l10n_pe_dte_status_response": '%s - %s' % (response[1]["success"]["data"].get('sunat_description', ''), response[1]["success"]["data"].get('sunat_note', '')) if has_sunat_notes else '',
                                "l10n_pe_dte_status":"accepted",
                            })

                        move.write(_invoice)
                    else:
                        if 'El comprobante fue previamente comunicado hacia nuestros servicios' in response[1]['error']['message']:
                            log.info('comprobante existe en portal de proveedor %s', self.name)
                            #TODO: Verficacion API REST de comprobante en portal de proveedor
                        raise ValidationError('%s\n\nInformacion tecnica:\n\n %s' % (response[1]["error"]["message"], json.dumps(response[1]["error"])))
                else:
                    raise UserError(response[1])
    
    def l10n_pe_dte_action_cancel(self):

        for move in self.filtered(
                lambda x: x.company_id.country_id.code == "PE" and
                            x.company_id.l10n_pe_edi_provider in ['conflux']):
            if move.l10n_pe_dte_conflux_uid:
                #data_dict = move._l10n_pe_prepare_dte_void_conflux()
                move.action_cancel()
                if move.state=="cancel":
                    response = self._send_json_to_conflux(token=move.company_id.l10n_pe_edi_pse_secret_key, data_dict={}, ws_url='https://einvoice.conflux.pe/api/v/1/account_einvoice/retention/%s/anular/' % move.l10n_pe_dte_conflux_uid)
                    if response[0]:
                        log.info(response[1])
                        if response[1].get("status")=="success":
                            move.write({
                                "l10n_pe_dte_void_status":'ask_for_status',
                                "l10n_pe_dte_cancel_reason": self._context.get('reason',_('Null document')),
                                "l10n_pe_dte_conflux_void_uid": response[1]["success"]["data"].get("resumen_de_reversion"),
                            })
                        else:
                            raise UserError(response[1]["error"]["message"])
                    else:
                        raise UserError(response[1])
                else:
                    raise UserError(_("It's not possible to cancel the despatch. Please check the log details \n Despatch: %s \n ")% (move.name))
            else:
                raise UserError(_("Comunicacion de baja no cuenta con el diario o identificador del PSE \n Reversion: %s \n ")% (move.name))

    def _l10n_pe_prepare_dte_withholding_conflux(self):
        dte_serial = ''
        dte_number = ''
        
        seq_split = self.name.split('-')
        if len(seq_split)==2:
            dte_serial = seq_split[0]
            dte_number = seq_split[1]

        conflux_dte = {
            'enviar': True,
            'enviar_automaticamente_a_la_sunat': True,
            "nombre_de_archivo": "%s-%s-%s-%s" % (self.company_id.vat, '20', dte_serial, dte_number),
            'proveedor_denominacion': self.partner_id.parent_id.name if self.partner_id.parent_id else self.partner_id.name,
            'proveedor_tipo_de_documento': self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            'proveedor_numero_de_documento': self.partner_id.vat,
            'proveedor_direccion': (self.partner_id.street_name or '') \
                                + (self.partner_id.street_number and (' ' + self.partner_id.street_number) or '') \
                                + (self.partner_id.street_number2 and (' ' + self.partner_id.street_number2) or '') \
                                + (self.partner_id.street2 and (' ' + self.partner_id.street2) or '') \
                                + (self.partner_id.l10n_pe_district and ', ' + self.partner_id.l10n_pe_district.name or '') \
                                + (self.partner_id.city_id and ', ' + self.partner_id.city_id.name or '') \
                                + (self.partner_id.state_id and ', ' + self.partner_id.state_id.name or '') \
                                + (self.partner_id.country_id and ', ' + self.partner_id.country_id.name or ''),
            'proveedor_correo': self.partner_id.email,
            'serie': dte_serial,
            'numero': dte_number,
            'moneda': 'PEN',
            'fecha_de_emision': self.date.strftime('%Y-%m-%d'),
            'tipo_de_tasa_de_retencion': self.l10n_pe_dte_withholding_type,
            'total_retenido':0,
            'total_pagado':0,
            'observaciones':'',
            'items':[]
        }
        
        for line in self.lines_ids:
            importe_retenido = 0
            importe_pagado_con_retencion = 0
            sequence = line.invoice_id.move_id.nro_comp.split('-')
            if line.type_document_id.code=='01' or line.type_document_id.code=='08':
                importe_retenido = line.amount_retention
                importe_pagado_con_retencion = line.debit-importe_retenido
                conflux_dte['items'].append({
                    "documento_relacionado_tipo": line.type_document_id.code,
                    "documento_relacionado_serie": sequence[0],
                    "documento_relacionado_numero": sequence[1],
                    "documento_relacionado_fecha_de_emision": line.invoice_date_it.strftime('%Y-%m-%d'),
                    "documento_relacionado_moneda": line.invoice_id.currency_id.name,
                    "documento_relacionado_total": abs(line.invoice_id.move_id.amount_total), #EN MONEDA DEL COMPROBANTE
                    "pago_fecha": line.payment_date.strftime('%Y-%m-%d'),
                    "pago_numero": "1",
                    #SE ESTA MODIFICANDO POR APURO
                    "pago_total_sin_retencion": line.debit if line.multipayment_line_id.currency_id.name=='PEN' else round(line.debit/line.tc,2), #EN MONEDA DEL COMPROBANTE
                    "tipo_de_cambio": line.tc,
                    "tipo_de_cambio_fecha": line.payment_date.strftime('%Y-%m-%d'),
                    "importe_retenido": importe_retenido, #EN SOLES
                    "importe_retenido_fecha": line.payment_date.strftime('%Y-%m-%d'),
                    "importe_pagado_con_retencion": importe_pagado_con_retencion, #EN SOLES
                })
            elif line.type_document_id.code=='07':
                conflux_dte['items'].append({
                    "documento_relacionado_tipo": line.type_document_id.code,
                    "documento_relacionado_serie": sequence[0],
                    "documento_relacionado_numero": sequence[1],
                    "documento_relacionado_fecha_de_emision": line.invoice_date_it.strftime('%Y-%m-%d'),
                    "documento_relacionado_moneda": line.invoice_id.move_id.currency_id.name,
                    "documento_relacionado_total": abs(line.invoice_id.move_id.amount_total), #EN MONEDA DEL COMPROBANTE
                })
            conflux_dte['total_retenido']+=importe_retenido
            conflux_dte['total_pagado']+=importe_pagado_con_retencion
        return conflux_dte
    
    def _send_json_to_conflux(self, token="", method="post", ws_url='https://einvoice.conflux.pe/api/v/1/account_einvoice/retention/', data_dict=None):
        s = requests.Session()
        if not ws_url:
            return (False, _("Conflux web service url not provided"))
        try:
            if method=='post':
                r = s.post(
                    ws_url,
                    headers={'Authorization': 'Token '+token},
                    json=data_dict)
            else:
                r = s.get(
                    ws_url,
                    headers={'Authorization': 'Token '+token},
                    json=data_dict)
        except requests.exceptions.RequestException as e:
            return (False, e)
        if r.status_code in (200,400):
            try:
                response = json.loads(r.content.decode())
                log.info(response)
            except ValueError as e:
                raise Warning(_("Exception decoding JSON response from Conflux: %s ", e))

            return (True, response)
        else:
            log.info(ws_url)
            log.info(token)
            log.info(data_dict)
            log.info(r.status_code)
            log.info(r.content)
            return (False, _("There's problems to connecte with Conflux Server"))