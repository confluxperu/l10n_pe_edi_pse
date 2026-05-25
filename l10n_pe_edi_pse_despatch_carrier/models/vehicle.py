# -*- encoding: utf-8 -*-
from odoo import fields, api, models, _

class Vehicle(models.Model):
    _inherit = 'l10n_pe_edi.vehicle'

    l10n_pe_edi_vehicle_tuc = fields.Char(string='TUC')