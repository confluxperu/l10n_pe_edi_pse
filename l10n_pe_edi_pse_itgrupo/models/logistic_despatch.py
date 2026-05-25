# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, _lt

import logging
log = logging.getLogger(__name__)

class LogisticDespatch(models.Model):
    _inherit = 'logistic.despatch'

    def _l10n_pe_prepare_dte(self):
        res = super(LogisticDespatch, self)._l10n_pe_prepare_dte()
        res.update({
            'origen_ubigeo': self.origin_address_id.district_id.code if self.origin_address_id.district_id else False,
            'origen_direccion': (self.origin_address_id.street_name or '') \
                                + (self.origin_address_id.street_number and (' ' + self.origin_address_id.street_number) or '') \
                                + (self.origin_address_id.street_number2 and (' ' + self.origin_address_id.street_number2) or '') \
                                + (self.origin_address_id.street2 and (' ' + self.origin_address_id.street2) or '') \
                                + (self.origin_address_id.district_id and ', ' + self.origin_address_id.district_id.name or '') \
                                + (self.origin_address_id.city_id and ', ' + self.origin_address_id.city_id.name or '') \
                                + (self.origin_address_id.state_id and ', ' + self.origin_address_id.state_id.name or '') \
                                + (self.origin_address_id.country_id and ', ' + self.origin_address_id.country_id.name or ''),
            'destino_ubigeo': self.delivery_address_id.district_id.code if self.delivery_address_id.district_id else False,
            'destino_direccion': (self.delivery_address_id.street_name or '') \
                                + (self.delivery_address_id.street_number and (' ' + self.delivery_address_id.street_number) or '') \
                                + (self.delivery_address_id.street_number2 and (' ' + self.delivery_address_id.street_number2) or '') \
                                + (self.delivery_address_id.street2 and (' ' + self.delivery_address_id.street2) or '') \
                                + (self.delivery_address_id.district_id and ', ' + self.delivery_address_id.district_id.name or '') \
                                + (self.delivery_address_id.city_id and ', ' + self.delivery_address_id.city_id.name or '') \
                                + (self.delivery_address_id.state_id and ', ' + self.delivery_address_id.state_id.name or '') \
                                + (self.delivery_address_id.country_id and ', ' + self.delivery_address_id.country_id.name or ''),
        })
        return res