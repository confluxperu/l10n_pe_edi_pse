# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, _lt

import logging
log = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_get_edi_values_conflux(self, invoice):
        res = super(AccountEdiFormat, self)._l10n_pe_edi_get_edi_values_conflux(invoice)
        if invoice.bo_order_purchase_service:
            res['orden_compra_servicio'] = invoice.bo_order_purchase_service
        res['total_gravada'] = invoice.amount_untaxed
        res['total'] = invoice.amount_total
        return res