# -*- coding: utf-8 -*-
{
    'name': "Integration EDI - IT Grupo Retenciones",
    'description': """
Integracion con emision de comprobantes de retencion con modulo itgrupo
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization',
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['l10n_pe_edi_pse_factura', 'l10n_pe_edi_pse_itgrupo','account_multipayment_supplier_retentions'],

    # always loaded
    'data': [
        'views/account_retention_comp.xml',
    ]
}
