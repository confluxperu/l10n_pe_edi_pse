# -*- coding: utf-8 -*-
{
    'name': 'EDI for Peru with PSE - Detracciones de transporte 027',
    'version': '18.0.1.0.0',
    'summary': 'Electronic Invoicing for Peru using direct connection with PSE - Detracciones de transporte 027',
    'category': 'Accounting/Localizations/EDI',
    'author': 'Obox',
    'license': 'Other proprietary',
'description': """
Extends EDI Peru Localization
=============================
- Support Invoices with detracciones de transporte 027
    """,
    'depends': [
        'sale',
        'l10n_pe_edi_pse_factura',
    ],
    "data": [
        "views/account_move_views.xml",
    ],
    'installable': True,
}