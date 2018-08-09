# -*- coding: utf-8 -*-
# Copyright (c) 2017 MINORISA <ramon.guiu@minorisa.net> 
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Factura simplificada para el SII vinculando el partner",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://odoo-community.org/",
    "author": "Minorisa S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {

    },
    "depends": [
        "min_l10n_es_aeat_sii",
    ],
    "data": [
        'views/res_partner_view.xml',
        'views/account_invoice_view.xml',
    ],
}