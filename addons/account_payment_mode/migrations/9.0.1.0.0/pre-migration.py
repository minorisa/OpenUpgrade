# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.addons.account_payment_mode.hooks import migrate_from_8
from openupgradelib import openupgrade


def migrate(cr, version=None):

    # Payment mode for account_invoice
    openupgrade.logged_query(
        cr, """
        UPDATE account_invoice
        SET payment_mode_id = payment_type
        """
    )

    # also support cases where openupgrade renamed the old module
    migrate_from_8(cr)
