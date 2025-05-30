# -*- encoding: utf-8 -*-
from odoo import fields, models, _
import logging
log = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_despatch(self):
        res = super(StockPicking, self)._prepare_despatch()
        res['l10n_pe_edi_origin_branch_code'] = self.location_id.l10n_pe_edi_branch_code if self.location_id.l10n_pe_edi_branch_code else ''
        res['l10n_pe_edi_delivery_branch_code'] = self.location_dest_id.l10n_pe_edi_branch_code if self.location_dest_id.l10n_pe_edi_branch_code else ''
        if self.location_dest_id.usage=='supplier' and self.partner_id:
            res['l10n_pe_edi_seller_supplier_id'] = self.partner_id.id
        if self.picking_type_id.code=='incoming':
            res['l10n_pe_edi_shipment_reason'] = '02'
        elif self.picking_type_id.code=='internal':
            res['l10n_pe_edi_shipment_reason'] = '04'
        if self.invoice_id:
            res['l10n_pe_edi_invoice_number'] = self.invoice_id.ref
        return res