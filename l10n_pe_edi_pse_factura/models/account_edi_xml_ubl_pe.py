from odoo import models
from odoo.tools import float_round, html_escape

class AccountEdiXmlUBLPE(models.AbstractModel):
    _inherit = 'account.edi.xml.ubl_pe'

    def _get_invoice_line_vals(self, line, taxes_vals, idx=None):
        vals = super()._get_invoice_line_vals(line, taxes_vals, idx)
        #price_precision = self.env['decimal.precision'].precision_get('Product Price')
        vals['line'] = line
        return vals