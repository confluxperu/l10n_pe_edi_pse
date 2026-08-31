# -*- coding: utf-8 -*-
{
    'name': "Peruvian - Electronic Carrier Delivery Note with PSE (Logistic)",

    'summary': """
        Adds Despatch Integration with carrier despatch.""",

    'description': """
        Adds Despatch Integration with carrier despatch.
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization/Peru',
    'version': '18.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['l10n_pe_edi_pse_despatch'],

    # always loaded
    'data': [
        'views/fleet_vehicle_views.xml',
        'views/logistic_despatch_view.xml',
    ]
}