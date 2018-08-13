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


tables_to_rename = [
    ('payment_mode', 'payment_mode_type'),
    ('payment_type', 'payment_mode')
]

xmlids_view = (
    'view_payment_type_tree',
    'view_payment_type_form',
    'action_payment_type',
)

xmlids_menu = (
    'menu_action_payment_type',
)


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_tables(cr, tables_to_rename)

    # First delete inherited views for payment type
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM ir_ui_view
        WHERE inherit_id IN (SELECT res_id FROM ir_model_data
            WHERE model = 'ir.ui.view' AND name IN %s) 
        """, (xmlids_view,)
    )
    # Delete views for payment type
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM ir_ui_view
        WHERE id IN (SELECT res_id FROM ir_model_data
            WHERE model = 'ir.ui.view' AND name IN %s) 
        """, (xmlids_view,)
    )
    # Delete menus for payment type
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM ir_ui_menu
        WHERE id IN (SELECT res_id FROM ir_model_data
            WHERE model = 'ir.ui.menu' AND name IN %s) 
        """, (xmlids_menu,)
    )
    # delete ir model data associated records
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM ir_model_data
        WHERE model = 'ir.ui.view'
        AND name in %s
        """, (xmlids_view,)
    )
    openupgrade.logged_query(
        cr,
        """
        DELETE FROM ir_model_data
        WHERE model = 'ir.ui.menu'
        AND name in %s
        """, (xmlids_menu,)
    )
