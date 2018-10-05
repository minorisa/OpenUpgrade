# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    openupgrade.logged_query(
        cr, """
        UPDATE res_country_state SET code = 'RN1'
        WHERE country_id = 32 AND code = 'RN';
        UPDATE res_country_state SET code = 'SP1'
        WHERE country_id = 32 AND code = 'SP';
        UPDATE res_country_state SET code = 'QC1'
        WHERE country_id = 39 AND code = 'QC'
        """
    )
