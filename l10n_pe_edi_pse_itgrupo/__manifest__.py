# -*- coding: utf-8 -*-
{
    'name': 'EDI for Peru with PSE - Itgrupo',
    'version': '1.0',
    'summary': 'Electronic Invoicing for Peru using direct connection with PSE - Itgrupo',
    'category': 'Accounting/Localizations/EDI',
    'author': 'Obox',
    'license': 'Other proprietary',
'description': """
Extends EDI Peru Localization for ITGrupo
=============================
- Support Invoices with itgrupo partner backoffice
    """,
    'depends': [
        'l10n_pe_edi_pse_factura',
        'l10n_pe_edi_pse_despatch'
    ],
    "data": [],
    'installable': True,
}