# -*- encoding: utf-8 -*-
from odoo import fields, models, _

class StockWarehouse(models.Model):
	_inherit = 'stock.warehouse'

	despatch_sequence_ids = fields.Many2many('ir.sequence', string='Despatch (Sequences)', copy=False)
