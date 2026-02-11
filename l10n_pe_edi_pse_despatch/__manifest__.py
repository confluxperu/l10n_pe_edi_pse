{
    'name': "Peruvian - Electronic Delivery Note with PSE (Logistic)",

    'summary': """
        Add Electronic Despatch integration.""",

    'description': """
        Add Electronic Despatch integration.
    """,

    'author': "Obox",
    'website': "https://obox.pe",
    'category': 'Localization/Peru',
    'version': '19.0.1.0.0',
    "depends": ["stock","l10n_pe_edi_pse_factura", "l10n_pe_edi_stock"],
    "data": [
        'data/sequences.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/logistic_despatch_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_warehouse_view.xml',
        'views/res_config_settings_view.xml',
    ],
}
