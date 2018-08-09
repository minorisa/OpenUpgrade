# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


column_renames = {
    'crm_helpdesk': [
        ('priority', None),
        ('channel_id', 'medium_id'),
    ],
}


@openupgrade.migrate()
def migrate(cr, version):
    pass
    # openupgrade.rename_columns(cr, column_renames)
