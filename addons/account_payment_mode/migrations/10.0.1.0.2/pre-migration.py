# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    if openupgrade.column_exists(cr, 'res_partner_bank', 'acc_type'):
        cr.execute('ALTER TABLE res_partner_bank DROP COLUMN acc_type')
