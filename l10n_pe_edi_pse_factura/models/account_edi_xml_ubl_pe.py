from odoo import models
from odoo.tools import float_round, html_escape
import logging
log = logging.getLogger(__name__)

class AccountEdiXmlUBLPE(models.AbstractModel):
    _inherit = 'account.edi.xml.ubl_pe'

    def _get_invoice_line_vals(self, line, taxes_vals, idx=None):
        vals = super()._get_invoice_line_vals(line, taxes_vals, idx)
        #price_precision = self.env['decimal.precision'].precision_get('Product Price')
        vals['line'] = line
        return vals

    def _add_invoice_tax_total_nodes(self, document_node, vals):
        super()._add_invoice_tax_total_nodes(document_node, vals)
        log.info('***************** _add_invoice_tax_total_nodes *****************')
        log.info(vals)