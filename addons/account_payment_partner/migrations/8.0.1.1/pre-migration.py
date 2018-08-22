# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011-TODAY MINORISA (http://www.minorisa.net)
#                             All Rights Reserved.
#                             Minorisa <contact@minorisa.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(cr, version):

    # Payment mode properties for res.partner
    openupgrade.logged_query(
        cr, """
        UPDATE ir_property
        SET value_reference = regexp_replace(
            value_reference, %(old_pattern)s, %(new_pattern)s
        ), name = 'supplier_payment_mode'
        WHERE name = 'payment_type_supplier'
        AND value_reference ~ %(old_pattern)s""", {
            'old_pattern': r"payment.type,[ ]*([0-9]*)",
            'new_pattern': r"^payment.mode,\1",
        }
    )
    openupgrade.logged_query(
        cr, """
        UPDATE ir_property
        SET value_reference = regexp_replace(
            value_reference, %(old_pattern)s, %(new_pattern)s
        ), name = 'customer_payment_mode'
        WHERE name = 'payment_type_customer'
        AND value_reference ~ %(old_pattern)s""", {
            'old_pattern': r"payment.type,[ ]*([0-9]*)",
            'new_pattern': r"^payment.mode,\1",
        }
    )

    # Payment mode for account_invoice
    openupgrade.logged_query(
        cr, """
        UPDATE account_invoice
        SET payment_mode_id = payment_type
        """
    )
