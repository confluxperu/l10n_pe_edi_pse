{
    'name': "Peruvian - Electronic Delivery Note with PSE (Logistic)",

    'summary': """
        Add Electronic Despatch integration.""",

    'description': """
        Add Electronic Despatch integration.
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",
    'category': 'Localization/Peru',
    'version': '18.0.1.0.0',
    "depends": ["logistic","l10n_pe_edi_pse_factura","l10n_pe_edi_stock"],
    "data": [
        'security/ir.model.access.csv',
        'views/logistic_despatch_view.xml',
        'views/stock_picking_view.xml',
    ],
}
