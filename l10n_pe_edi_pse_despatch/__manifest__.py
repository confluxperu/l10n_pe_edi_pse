{
    'name': "Peruvian - Electronic Delivery Note with PSE (Logistic)",

    'summary': """
        Add Electronic Despatch integration.""",

    'description': """
        Add Electronic Despatch integration.
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization/Peru',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    "depends": ["logistic","l10n_pe_edi_pse_factura","l10n_pe_edi_stock"],
    
    # always loaded
    "data": [
        'security/ir.model.access.csv',
        'views/logistic_despatch_view.xml',
        'views/stock_location_view.xml',
        'views/stock_picking_view.xml',
    ],
}
