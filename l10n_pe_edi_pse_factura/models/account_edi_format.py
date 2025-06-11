# -*- coding: utf-8 -*-

import base64
import zipfile
import io
import requests
import json
from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, InvalidURL, ReadTimeout
from lxml import etree
from lxml.objectify import fromstring
from copy import deepcopy

from odoo import models, fields, api, _, _lt
from odoo.addons.iap.tools.iap_tools import iap_jsonrpc
from odoo.exceptions import AccessError
from odoo.tools import float_round, html_escape

import logging
log = logging.getLogger(__name__)

DEFAULT_CONFLUX_FACTURA_ENDPOINT = 'https://einvoice.conflux.pe/api/v/1/account_einvoice/invoice/'
DEFAULT_CONFLUX_FACTURA_ESTADO_ENDPOINT = 'http://einvoice.conflux.pe/api/v/1/account_einvoice/invoice/%s/status/'
DEFAULT_CONFLUX_FACTURA_BAJA_ENDPOINT = 'https://einvoice.conflux.pe/api/v/1/account_einvoice/void/'

def request_json(token="", method="post", url=None, data_dict=None):
    s = requests.Session()
    if not url:
        raise InvalidURL(_("Url not provided"))
    try:
        if method=='post':
            r = s.post(
                url,
                headers={'Authorization': 'Token '+token},
                json=data_dict)
        else:
            r = s.get(
                url,
                headers={'Authorization': 'Token '+token},
                json=data_dict)
    except requests.exceptions.RequestException as e:
        log.info(data_dict)
        return {"message":_("Exception: %s" % e)}
    if r.status_code in (200,400):
        log.info(data_dict)
        try:
            response = json.loads(r.content.decode())
            log.info(response)
        except ValueError as e:
            return {"message":_("Exception decoding JSON response: %s" % e)}
        return response
    else:
        log.info(url)
        log.info(token)
        log.info(data_dict)
        log.info(r.status_code)
        log.info(r.content)
        return {"message":_("There's problems to connect with PSE Server")}


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    @api.model
    def _l10n_pe_edi_pse_create_attachment(self, documents):
        attachment = self.env['ir.attachment']
        attachment_ids = []
        for filename, url, company in documents:
            created = attachment.create({
                "name":filename,
                "type":'url',
                "url":url,
                "public":True,
                "company_id": company.id
            })
            attachment_ids.append(created.id)
        return attachment_ids

    def _l10n_pe_edi_get_edi_values_conflux(self, invoice):
        price_precision = self.env['decimal.precision'].precision_get('Product Price')
        builder = self.env['account.edi.xml.ubl_pe']
        invoice_vals = builder._export_invoice_vals(invoice)
        base_dte = builder._export_invoice_vals(invoice)

        record = base_dte.get('invoice')

        invoice_sequence = record.name.replace(' ','').split('-')
        
        dte_serial = ''
        dte_number = ''
        if len(invoice_sequence)==2:
            dte_serial = invoice_sequence[0]
            dte_number = invoice_sequence[1]

        conflux_dte = {
            "enviar":True,
            "nombre_de_archivo": "%s-%s-%s-%s" % (record.company_id.vat, record.l10n_latam_document_type_id.code, dte_serial, dte_number),
            "cliente_tipo_de_documento":record.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            "cliente_numero_de_documento":record.partner_id.vat,
            "cliente_denominacion": record.partner_id.name,
            "cliente_direccion": (record.partner_id.street or '') \
                                + (record.partner_id.l10n_pe_district and ', ' + record.partner_id.l10n_pe_district.name or '') \
                                + (record.partner_id.city_id and ', ' + record.partner_id.city_id.name or '') \
                                + (record.partner_id.state_id and ', ' + record.partner_id.state_id.name or '') \
                                + (record.partner_id.country_id and ', ' + record.partner_id.country_id.name or ''),
            "cliente_email": record.partner_id.email if record.partner_id.email else '',
            "fecha_de_emision": base_dte['vals'].get('issue_date').strftime('%Y-%m-%d'),
            "tipo_de_operacion": record.l10n_pe_edi_operation_type,
            "tipo_de_comprobante": record.l10n_latam_document_type_id.code,
            "serie": dte_serial,
            "numero": dte_number,
            "forma_de_pago_credito":False,
            "credito_cuotas":[],
            "moneda": record.currency_id.name,
            #"tipo_de_cambio": round(base_dte.get('currency_rate',1),3),
            "total_gravada": 0,
            "total_exonerada": 0,
            "total_inafecta": 0,
            "total_gratuita": 0,
            "total_exportacion": 0,
            "total_prepagado": 0,
            "total_igv": 0,
            "total_isc": 0,
            "total_icbper": 0,
            #"total_otros": 0,
            "total": 0,
            "descuento_base": 0,
            "descuento_importe": 0,
            "total_otros_cargos": 0,
            "items": []
        }

        if base_dte['taxes_vals']['base_amount_currency']!=0:
            conflux_dte['tipo_de_cambio'] = base_dte['taxes_vals']['base_amount']/base_dte['taxes_vals']['base_amount_currency']

        if base_dte['vals'].get('payment_terms_vals', []):
            for payment_terms in base_dte['vals']['payment_terms_vals']:
                if payment_terms['payment_means_id'] == 'Credito':
                    conflux_dte['forma_de_pago_credito'] = True
                if payment_terms['id'] == 'Detraccion':
                    conflux_dte["detraccion"]=True
                    conflux_dte["total_detraccion"]=payment_terms['amount']
                    conflux_dte["porcentaje_detraccion"]=payment_terms['payment_percent']
                    conflux_dte["codigo_detraccion"]=payment_terms['payment_means_id']
                    conflux_dte['medio_de_pago_detraccion']='999'

        for tax_total in base_dte['vals']['tax_total_vals']:
            for tax_subtotal in tax_total['tax_subtotal_vals']:
                if tax_subtotal['tax_category_vals']['tax_scheme_vals']['name']=='IGV':
                    conflux_dte['total_gravada']+=tax_subtotal['taxable_amount']
                    conflux_dte['total_igv']+=tax_subtotal['tax_amount']
                if tax_subtotal['tax_category_vals']['tax_scheme_vals']['name']=='EXO':
                    conflux_dte['total_exonerada']+=tax_subtotal['taxable_amount']
                if tax_subtotal['tax_category_vals']['tax_scheme_vals']['name']=='INA':
                    conflux_dte['total_inafecta']+=tax_subtotal['taxable_amount']
                if tax_subtotal['tax_category_vals']['tax_scheme_vals']['name']=='GRA':
                    conflux_dte['total_gratuita']+=tax_subtotal['taxable_amount']
                if tax_subtotal['tax_category_vals']['tax_scheme_vals']['name']=='EXP':
                    conflux_dte['total_exportacion']+=tax_subtotal['taxable_amount']
                if tax_subtotal['tax_category_vals']['tax_scheme_vals']['name']=='ISC':
                    conflux_dte['total_isc']+=tax_subtotal['tax_amount']
                if tax_subtotal['tax_category_vals']['tax_scheme_vals']['name']=='ICBPER':
                    conflux_dte['total_icbper']+=tax_subtotal['tax_amount']
                if tax_subtotal['tax_category_vals']['tax_scheme_vals']['name']=='OTROS':
                    conflux_dte['total_otros_cargos']+=tax_subtotal['tax_amount']

        if round(conflux_dte['total_gravada'],2)==-0.01:
            conflux_dte['total_gravada'] = 0
        
        conflux_dte['total'] = conflux_dte['total_gravada']+conflux_dte['total_igv']+conflux_dte['total_exonerada']+conflux_dte['total_inafecta']+conflux_dte['total_exportacion']+conflux_dte['total_isc']+conflux_dte['total_icbper']

        descuento_importe_02 = 0
        descuento_importe_03 = 0
        descuento_base = 0

        if base_dte['vals'].get('line_vals'):
            for invoice_line in base_dte['vals'].get('line_vals', []):
                line = invoice_line.get('line')
                igv_type = '10'
                isc_type = ''
                is_free = False
                is_exo_or_unaffected = False

                igv_amount = 0
                isc_amount = 0
                icbper_amount = 0

                for tax_total in invoice_line['tax_total_vals']:
                    for tax in tax_total['tax_subtotal_vals']:
                        if tax['tax_category_vals']['tax_scheme_vals']['name'] == 'IGV':
                            igv_amount+=tax['tax_amount']
                        if tax['tax_category_vals']['tax_scheme_vals']['name'] == 'ISC':
                            isc_type = tax['tax_category_vals']['tier_range']
                            isc_amount+=tax['tax_amount']
                        if tax['tax_category_vals']['tax_scheme_vals']['name'] == 'ICBPER':
                            icbper_amount+=tax['tax_amount']
                        if tax['tax_category_vals']['tax_scheme_vals']['name'] in ('IGV','EXO','INA','EXP','GRA'):
                            igv_type = tax['tax_category_vals']['tax_exemption_reason_code']
                            if tax['tax_category_vals']['tax_scheme_vals']['name'] in ('EXO','INA','EXP'):
                                is_exo_or_unaffected = True
                        if tax['tax_category_vals']['tax_scheme_vals']['name'] == 'GRA':
                            is_free = True

                if is_free:
                    conflux_dte['total_isc']-=isc_amount
                    conflux_dte['total']-=isc_amount

                if line.price_subtotal<0 and line.l10n_pe_edi_allowance_charge_reason_code in ('02','00'):
                    descuento_importe_02+=abs(line.price_subtotal)
                    continue
                if line.price_subtotal<0 and not line.l10n_pe_edi_downpayment_line and (line.l10n_pe_edi_allowance_charge_reason_code=='03' or is_exo_or_unaffected):
                    descuento_importe_03+=abs(line.price_subtotal)
                    continue
                if not line.l10n_pe_edi_downpayment_line and line.price_subtotal<0:
                    descuento_importe_02+=abs(line.price_subtotal)
                    continue
                else:
                    descuento_base+=abs(line.price_subtotal)
                    default_uom = 'NIU'
                    if line.product_id.type=='service':
                        default_uom = 'ZZ'

                    valor_unitario = float_round(line.price_subtotal / abs(line.quantity), precision_digits=price_precision) if line.quantity else 0.0
                    precio_unitario = float_round(line.price_total / abs(line.quantity), precision_digits=price_precision) if line.quantity else 0.0
                    if line.discount==100:
                        '''
                        taxes_res = line.tax_ids.compute_all(
                            line.price_unit,
                            quantity=1,
                            currency=line.currency_id,
                            product=line.product_id,
                            partner=line.partner_id,
                            is_refund=line.is_refund,
                        )
                        precio_unitario = taxes_res['total_included']
                        valor_unitario = taxes_res['total_excluded']
                        '''
                        precio_unitario = line.price_unit
                        valor_unitario = line.price_unit
                        if igv_type=='10':
                            igv_type = '32'
                        is_free = True
                    _item = {
                        "codigo":line.product_id.default_code if line.product_id.default_code else '',
                        "codigo_producto_sunat":line.product_id.unspsc_code_id.code if line.product_id.unspsc_code_id else '',
                        "descripcion":line.name.replace('[%s] ' % line.product_id.default_code,'') if line.product_id else line.name,
                        "cantidad":abs(invoice_line['line_quantity']),
                        "unidad_de_medida":line.product_uom_id.l10n_pe_edi_measure_unit_code if line.product_uom_id.l10n_pe_edi_measure_unit_code else default_uom,
                        'valor_unitario': valor_unitario,
                        'precio_unitario': precio_unitario,
                        "subtotal":line.price_subtotal if not is_free else 0,
                        "total":line.price_total if not is_free else icbper_amount,
                        "tipo_de_igv": igv_type,
                        "igv":igv_amount,
                        "isc":isc_amount,
                        "icbper":icbper_amount,
                        "gratuito":is_free,
                    }

                    if line.discount>0 and line.discount<100:
                        _item['descuento_tipo']=line.l10n_pe_edi_allowance_charge_reason_code if line.l10n_pe_edi_allowance_charge_reason_code else '00'
                        _item['descuento_factor']=(line.discount or 0.0) / 100.0
                        _item['descuento_base']=line.price_subtotal/(1.0 - _item['descuento_factor'])
                        _item['descuento_importe']=_item['descuento_base'] * _item['descuento_factor']

                    if isc_amount>0:
                        _item['tipo_de_calculo_isc'] = isc_type

                    if line.l10n_pe_edi_downpayment_line and line.price_subtotal<0:
                        _item['anticipo_regularizacion'] = line.l10n_pe_edi_downpayment_line
                        _item['anticipo_numero_de_documento'] = line.l10n_pe_edi_downpayment_ref_number
                        _item['anticipo_tipo_de_documento'] = line.l10n_pe_edi_downpayment_ref_type
                        if line.l10n_pe_edi_downpayment_date:
                            _item['anticipo_fecha'] = line.l10n_pe_edi_downpayment_date.strftime('%Y-%m-%d')
                        conflux_dte['total_prepagado']+=abs(line.price_total)
                    conflux_dte['items'].append(_item)

        if conflux_dte['total_prepagado']>0:
            if abs(round(conflux_dte['total_gravada'],2))<=0.01:
                conflux_dte['total_gravada'] = 0
            if abs(round(conflux_dte['total_igv'],2))<=0.01:
                conflux_dte['total_igv'] = 0
            if abs(round(conflux_dte['total'],2))<=0.01:
                conflux_dte['total'] = 0

        if record.ref and record.l10n_latam_document_type_id.internal_type == 'invoice':
            conflux_dte['orden_compra_servicio'] = record.ref[:20]
        if record.partner_id.email:
            conflux_dte['cliente_email'] = record.partner_id.email
        if record.narration and record.narration!='':
            conflux_dte['observaciones'] = record.narration
        if record.company_id.l10n_pe_edi_address_type_code and record.company_id.l10n_pe_edi_address_type_code!='0000':
            conflux_dte['establecimiento_anexo'] = record.company_id.l10n_pe_edi_address_type_code
        if record.invoice_user_id:
            conflux_dte['vendedor'] = record.invoice_user_id.name
        if record.invoice_payment_term_id:
            conflux_dte['condiciones_de_pago'] = record.invoice_payment_term_id.name

        if descuento_importe_02>0:
            conflux_dte["descuento_tipo"]="02"
            conflux_dte["descuento_base"]=descuento_base
            conflux_dte["descuento_importe"]=descuento_importe_02
            conflux_dte["descuento_factor"]=descuento_importe_02/descuento_base
        
        if descuento_importe_03>0:
            conflux_dte["descuento_tipo"]="03"
            conflux_dte["descuento_base"]=descuento_base
            conflux_dte["descuento_importe"]=descuento_importe_03
            conflux_dte["descuento_factor"]=descuento_importe_03/descuento_base

        if record.l10n_latam_document_type_id.code=='07':
            conflux_dte['tipo_de_nota_de_credito'] = record.l10n_pe_edi_refund_reason
            conflux_dte['documento_que_se_modifica_tipo'] = record.l10n_pe_edi_rectification_ref_type.code
            conflux_dte['documento_que_se_modifica_numero'] = record.l10n_pe_edi_rectification_ref_number
            if record.l10n_pe_edi_rectification_ref_date:
                conflux_dte['documento_que_se_modifica_fecha'] = record.l10n_pe_edi_rectification_ref_date.strftime('%Y-%m-%d')
        
        if record.l10n_latam_document_type_id.code=='08':
            conflux_dte['tipo_de_nota_de_debito'] = record.l10n_pe_edi_charge_reason
            conflux_dte['documento_que_se_modifica_tipo'] = record.l10n_pe_edi_rectification_ref_type.code
            conflux_dte['documento_que_se_modifica_numero'] = record.l10n_pe_edi_rectification_ref_number
            if record.l10n_pe_edi_rectification_ref_date:
                conflux_dte['documento_que_se_modifica_fecha'] = record.l10n_pe_edi_rectification_ref_date.strftime('%Y-%m-%d')

        if record.l10n_latam_document_type_id.code=='01' and record.invoice_date_due:
            conflux_dte['fecha_de_vencimiento'] = record.invoice_date_due.strftime('%Y-%m-%d')

        payment_fee_id = 0
        for payment_fee in record.l10n_pe_edi_payment_fee_ids:
            payment_fee_id+=1
            conflux_dte['credito_cuotas'].append({
                'codigo':"Cuota" + str(payment_fee_id).zfill(3),
                'fecha_de_vencimiento':payment_fee.date_due.strftime('%Y-%m-%d'),
                'importe_a_pagar':payment_fee.amount_total,
            })

        #spot = record._l10n_pe_edi_get_spot()
        
        retention = record._l10n_pe_edi_get_retention()
        if retention and retention['retention_amount']>0:
            conflux_dte["retencion_tipo"]=retention['retention_type']
            conflux_dte["total_retencion"]=retention['retention_amount']
            conflux_dte["retencion_base_imponible"]=retention['retention_base']

        if record.l10n_pe_edi_transportref_ids:
            conflux_dte['guias'] = []
            for despatch in record.l10n_pe_edi_transportref_ids:
                conflux_dte['guias'].append({
                    'guia_tipo': despatch.ref_type,
                    'guia_serie_numero': despatch.ref_number
                })
        return conflux_dte

    def _l10n_pe_edi_sign_invoices_conflux(self, invoice, edi_filename, edi_str=''):
        if self.code != 'pe_pse':
            return {'error': 'Para envio a SUNAT mediante PSE el diario debe tener tener activo el campo Facturacion Electronica como "Peru PSE"', 'blocking_level': 'warning'}
        if invoice.l10n_pe_edi_pse_uid:
            service_iap = self._l10n_pe_edi_sign_service_step_2_conflux(
                invoice.company_id, invoice.l10n_pe_edi_pse_uid)
        else:
            edi_conflux_values = self._l10n_pe_edi_get_edi_values_conflux(invoice)
            service_iap = self._l10n_pe_edi_sign_service_step_1_conflux(
                invoice.company_id, edi_conflux_values, invoice.l10n_latam_document_type_id.code,
                invoice._l10n_pe_edi_get_serie_folio())
        if service_iap.get('extra_msg'):
            invoice.message_post(body=service_iap['extra_msg'])
        update_invoice = {}
        if service_iap.get('pse_status', False):
            update_invoice['l10n_pe_edi_pse_status'] = service_iap.get('pse_status')
        if service_iap.get('uid', False):
            update_invoice['l10n_pe_edi_pse_uid'] = service_iap.get('uid')
        if not invoice.l10n_pe_edi_pse_uid:
            if service_iap.get('xml_url'):
                attachment_xml_id = self._l10n_pe_edi_pse_create_attachment([('%s.xml' % edi_filename, service_iap['xml_url'], invoice.company_id)])
                update_invoice['l10n_pe_edi_xml_file'] = attachment_xml_id[0]
                service_iap['xml_attachment_id'] = update_invoice['l10n_pe_edi_xml_file']
            if service_iap.get('pdf_url'):
                attachment_pdf_id = self._l10n_pe_edi_pse_create_attachment([('%s.pdf' % edi_filename, service_iap['pdf_url'], invoice.company_id)])
                update_invoice['l10n_pe_edi_pdf_file'] = attachment_pdf_id[0]
        if update_invoice.get('l10n_pe_edi_pse_status', False) in ('accepted','objected'):
            if service_iap.get('cdr_url'):
                attachment_cdr_id = self._l10n_pe_edi_pse_create_attachment([('CDR-%s.xml' % edi_filename, service_iap['cdr_url'], invoice.company_id)])
                update_invoice['l10n_pe_edi_cdr_file'] = attachment_cdr_id[0]
        if update_invoice:
            invoice.write(update_invoice)
        return service_iap
    
    def _l10n_pe_edi_post_invoice_web_service_pse(self, invoice, edi_filename, edi_str):
        provider = invoice.company_id.l10n_pe_edi_provider
        res = getattr(self, '_l10n_pe_edi_sign_invoices_%s' % provider)(invoice, edi_filename, edi_str)

        if res.get('error'):
            return res

        # Chatter.
        documents_xml = []
        documents = []
        '''if res.get('xml_url'):
            documents_xml.append(('%s.xml' % edi_filename, res['xml_url']))
        if res.get('cdr_url'):
            documents.append(('CDR-%s.xml' % edi_filename, res['cdr_url']))
        if res.get('pdf_url'):
            documents.append(('%s.pdf' % edi_filename, res['pdf_url']))'''
        if res.get('xml_attachment_id'):
            '''zip_edi_str = self._l10n_pe_edi_zip_edi_document(documents)
            res['attachment'] = self.env['ir.attachment'].create({
                'res_model': invoice._name,
                'res_id': invoice.id,
                'type': 'binary',
                'name': '%s.zip' % edi_filename,
                'datas': base64.encodebytes(zip_edi_str),
                'mimetype': 'application/zip',
            })'''
            #edit_attachment_xml_id = self._l10n_pe_edi_pse_create_attachment(documents_xml)
            res['attachment'] = self.env['ir.attachment'].browse(res['xml_attachment_id'])

            #edi_attachment_ids = self._l10n_pe_edi_pse_create_attachment(documents+edit_attachment_xml_id)
            message = _("The EDI document was successfully created and signed by the government.")
            invoice.with_context(no_new_invoice=True).message_post(
                body=message,
                #attachment_ids=edi_attachment_ids,
            )

        return res

    def _l10n_pe_edi_sign_service_step_2_conflux(self, company, uid_invoice):
        try:
            result = request_json(url=DEFAULT_CONFLUX_FACTURA_ESTADO_ENDPOINT % uid_invoice, method='get', token=company.l10n_pe_edi_pse_secret_key, data_dict={})
        except InvalidSchema:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE16'], 'blocking_level': 'error'}
        except AccessError:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE17'], 'blocking_level': 'warning'}
        except InvalidURL:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE18'], 'blocking_level': 'error'}

        if result.get('message') and result.get('status')=='error':
            if result['message'] == 'no-credit':
                error_message = self._l10n_pe_edi_get_iap_buy_credits_message(company)
            else:
                error_message = 'Error al consultar estado de documento: %s' % result['message']
            return {'error': error_message, 'blocking_level': 'error'}

        xml_url = None
        cdr_url = None
        pdf_url = None
        success = False
        extra_msg = ''
        edi_status = 'ask_for_status'
        if result.get('emision_aceptada', False):
            edi_status = 'accepted'
            success = True
            if result.get('enlace_del_cdr', False):
                cdr_url = result['enlace_del_cdr']
        if result.get('emision_rechazada', False):
            extra_msg = '%s - %s' % (result.get('sunat_description', ''), result.get('sunat_note', '')), 
            edi_status = 'rejected'
            success = True
            
        return {
            'success':success,
            'xml_url':xml_url,
            'pdf_url':pdf_url,
            'cdr_url':cdr_url,
            'pse_status': edi_status,
            'extra_msg': extra_msg
        }

    def _l10n_pe_edi_sign_invoice_pse(self, invoice):
        if invoice.l10n_pe_edi_pse_uid:
            #self.state = 'sent'
            return {invoice:{'success':True}}
        edi_filename = '%s-%s-%s' % (
            invoice.company_id.vat,
            invoice.l10n_latam_document_type_id.code,
            invoice.name.replace(' ', ''),
        )
        latam_invoice_type = self._get_latam_invoice_type(invoice.l10n_latam_document_type_id.code)
        edi_str = ''

        if not latam_invoice_type:
            return {invoice: {'error': _("Missing LATAM document code.")}}

        res = self._l10n_pe_edi_post_invoice_web_service_pse(invoice, edi_filename, edi_str)

        return {invoice: res}

    def _l10n_pe_edi_cancel_invoices_pse(self, invoices):
        # OVERRIDE
        if self.code != 'pe_pse':
            return super()._cancel_invoice_edi(invoices)

        invoice = invoices # Batching is disabled for this EDI.
        edi_attachments = self.env['ir.attachment']
        res = {}
        if not invoice.l10n_pe_edi_cancel_reason:
            return {invoice: {'error': _("Please put a cancel reason")}}

        edi_attachments |= invoice._get_edi_attachment(self)

        res = {}
        if invoice.l10n_pe_edi_pse_cancel_uid:
            # Cancel part 2: Get Cancel Comunication Status.
            res.update(self._l10n_pe_edi_pse_cancel_invoice_edi_step_2(invoice))
        else:
            # Cancel part 1: Send Cancel Communication.
            res.update(self._l10n_pe_edi_pse_cancel_invoice_edi_step_1(invoice))

        return res
        

    def _l10n_pe_edi_sign_service_step_1_conflux(self, company, data_dict, latam_document_type, serie_folio):
        try:
            result = request_json(url=DEFAULT_CONFLUX_FACTURA_ENDPOINT, method='post', token=company.l10n_pe_edi_pse_secret_key, data_dict=data_dict)
        except InvalidSchema:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE16'], 'blocking_level': 'error'}
        except AccessError:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE17'], 'blocking_level': 'warning'}
        except InvalidURL:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE18'], 'blocking_level': 'error'}

        if result.get('message') and result.get('status')=='error':
            log.info(data_dict)
            if result['message'] == 'no-credit':
                error_message = self._l10n_pe_edi_get_iap_buy_credits_message(company)
            else:
                error_message = '%s - [LOG: %s]' % (result['message'], json.dumps(result))
            return {'error': error_message, 'blocking_level': 'error'}

        xml_url = None
        cdr_url = None
        pdf_url = None
        success = False
        if result.get('status')=='success':
            edi_status = 'ask_for_status'
            success = True
            if result['success']['data'].get('enlace_del_xml', False):
                xml_url = result['success']['data']['enlace_del_xml']
            if result['success']['data'].get('enlace_del_pdf', False):
                pdf_url = result['success']['data']['enlace_del_pdf']
            if result['success']['data'].get('emision_aceptada', False):
                edi_status = 'accepted'
                success = True
                if result['success']['data'].get('enlace_del_cdr', False):
                    cdr_url = result['success']['data']['enlace_del_cdr']
            if result['success']['data'].get('emision_rechazada', False):
                log.info(data_dict)
                edi_status = 'rejected'
                success = True
                error_message = result['success']['data']['sunat_description']
                
            return {
                'success':success,
                'uid':result['success']['data']['uid'],
                'xml_url':xml_url,
                'pdf_url':pdf_url,
                'cdr_url':cdr_url,
                'pse_status': edi_status,
                'extra_msg': error_message if edi_status == 'rejected' else ''
            }
        extra_msg = error_message
        return {'xml_url': xml_url, 'cdr_url': cdr_url, 'extra_msg': extra_msg}
    
    def _l10n_pe_edi_pse_cancel_invoices_step_1_conflux(self, company, invoice):
        self.ensure_one()
        try:
            result = request_json(url=DEFAULT_CONFLUX_FACTURA_BAJA_ENDPOINT, method='post', token=company.l10n_pe_edi_pse_secret_key, data_dict={'id':invoice.l10n_pe_edi_pse_uid})
        except AccessError:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE17'], 'blocking_level': 'warning'}
        except KeyError:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE18'], 'blocking_level': 'error'}

        if result.get('message') and result.get('status')=='error':
            error_message = result['message']
            return {'error': error_message, 'blocking_level': 'error'}

        void_uid = 'VOID-%s' % invoice.l10n_pe_edi_pse_uid

        edi_void_status = 'ask_for_status'

        return {'void_uid': void_uid, 'pse_void_status':edi_void_status}

    def _l10n_pe_edi_pse_cancel_invoices_step_2_conflux(self, company, invoice):
        try:
            result = request_json(url=DEFAULT_CONFLUX_FACTURA_ESTADO_ENDPOINT % invoice.l10n_pe_edi_pse_uid, method='get', token=company.l10n_pe_edi_pse_secret_key, data_dict={})
        except KeyError:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE18'], 'blocking_level': 'error'}
        except AccessError:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE17'], 'blocking_level': 'warning'}

        if result.get('message') and result.get('status')=='error':
            if result['message'] == 'no-credit':
                error_message = self._l10n_pe_edi_get_iap_buy_credits_message(company)
            else:
                error_message = result['message']
            return {'error': error_message, 'blocking_level': 'error'}

        extra_msg = ''
        edi_void_status = 'ask_for_status'
        if result.get('baja_aceptada', False):
            edi_void_status = 'accepted'
        if result.get('baja_rechazada', False):
            extra_msg = _('The EDI document failed to be cancelled')
            edi_void_status = 'rejected'

        return {'success': True, 'cdr': 'CDR-NO-DISPONIBLE','pse_void_status':edi_void_status,'extra_msg': extra_msg}

    def _l10n_pe_edi_pse_cancel_invoice_edi_step_1(self, invoice):
        self.ensure_one()
        company = invoice[0].company_id # documents are always batched by company in account_edi.
        provider = company.l10n_pe_edi_provider

        void_filename = '%s-%s-%s' % (
            invoice.company_id.vat,
            invoice.l10n_latam_document_type_id.code,
            invoice.name.replace(' ', ''),
        )

        res = getattr(self, '_l10n_pe_edi_pse_cancel_invoices_step_1_%s' % provider)(company, invoice)

        if res.get('error'):
            return {invoice: res}

        if not res.get('void_uid'):
            error = _("The EDI document failed to be cancelled because the cancellation Void identifier is missing.")
            return {invoice: {'error': error}}

        # Chatter.
        message = _("Cancellation is in progress in the government side (Void identifier: %s).", html_escape(res['void_uid']))
        if res.get('xml_document'):
            '''void_attachment = self.env['ir.attachment'].create({
                'type': 'binary',
                'name': 'VOID-%s.xml' % void_filename,
                'datas': base64.encodebytes(res['xml_document']),
                'mimetype': 'application/xml',
            })'''
            invoice.with_context(no_new_invoice=True).message_post(
                body=message,
                #attachment_ids=void_attachment.ids,
            )

        invoice.write({'l10n_pe_edi_pse_cancel_uid': res['void_uid'], 'l10n_pe_edi_pse_void_status':res['pse_void_status']})
        #return {invoice: {'error': message, 'blocking_level': 'info'}}
        return {invoice: {'success': True}}

    def _l10n_pe_edi_pse_cancel_invoice_edi_step_2(self, invoice):
        self.ensure_one()
        company = invoice.company_id
        provider = company.l10n_pe_edi_provider

        res = getattr(self, '_l10n_pe_edi_pse_cancel_invoices_step_2_%s' % provider)(company, invoice)

        if res.get('error'):
            return {invoice: res}
        if not res.get('success'):
            error = _("The EDI document failed to be cancelled for unknown reason.")
            return {invoice: {'error': error}}

        # Chatter.
        message = _("The EDI document was successfully cancelled by the government (Void identifier: %s).", html_escape(invoice.l10n_pe_edi_pse_cancel_uid))
        invoice.with_context(no_new_invoice=True).message_post(
            body=message,
        )
        return {invoice: {'success': True}}

    # -------------------------------------------------------------------------
    # EDI OVERRIDDEN METHODS
    # -------------------------------------------------------------------------

    def _get_move_applicability(self, move):
        # EXTENDS account_edi
        self.ensure_one()
        if self.code != 'pe_pse':
            if self.code == 'pe_ubl_2_1':
                return {}
            return super()._get_move_applicability(move)

        if move.l10n_pe_edi_is_required:
            return {
                'post': self._l10n_pe_edi_sign_invoice_pse,
                'cancel': self._l10n_pe_edi_cancel_invoices_pse,
                #'cancel_batching': lambda invoice: (invoice.l10n_pe_edi_cancel_cdr_number,),
                #'edi_content': self._l10n_pe_edi_xml_invoice_content,
            }

    def _needs_web_services(self):
        # OVERRIDE
        return self.code == 'pe_pse' or super()._needs_web_services()

    def _check_move_configuration(self, move):
        # OVERRIDE
        res = super()._check_move_configuration(move)
        if self.code != 'pe_pse':
            return res

        if not move.company_id.vat:
            res.append(_("VAT number is missing on company %s") % move.company_id.display_name)
        lines = move.invoice_line_ids.filtered(lambda line: not line.display_type)
        for line in lines:
            taxes = line.tax_ids
            if len(taxes) > 1 and len(taxes.filtered(lambda t: t.tax_group_id.l10n_pe_edi_code == 'IGV')) > 1:
                res.append(_("You can't have more than one IGV tax per line to generate a legal invoice in Peru"))
        if any(not line.tax_ids for line in move.invoice_line_ids if not line.display_type):
            res.append(_("Taxes need to be assigned on all invoice lines"))

        return res

    def _is_compatible_with_journal(self, journal):
        # OVERRIDE
        if self.code != 'pe_pse':
            return super()._is_compatible_with_journal(journal)
        return journal.type == 'sale' and journal.country_code == 'PE' and journal.l10n_latam_use_documents