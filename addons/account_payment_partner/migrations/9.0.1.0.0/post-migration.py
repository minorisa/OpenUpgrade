# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):

    # Payment mode properties for res.partner
    openupgrade.logged_query(
        env.cr, """
        UPDATE ir_property
        SET value_reference = regexp_replace(
            value_reference, %(old_pattern)s, %(new_pattern)s
        ),
        name = 'supplier_payment_mode_id',
        fields_id = (
            SELECT id FROM ir_model_fields
            WHERE name = 'supplier_payment_mode_id'
              AND model = 'res.partner' AND ttype = 'many2one'
        )
        WHERE name = 'payment_type_supplier'
        AND value_reference ~ %(old_pattern)s""", {
            'old_pattern': r"^payment.type,[ ]*([0-9]*)",
            'new_pattern': r"account.payment.mode,\1",
        }
    )
    openupgrade.logged_query(
        env.cr, """
        UPDATE ir_property
        SET value_reference = regexp_replace(
            value_reference, %(old_pattern)s, %(new_pattern)s
        ), name = 'customer_payment_mode_id',
        fields_id = (
            SELECT id FROM ir_model_fields
            WHERE name = 'customer_payment_mode_id'
              AND model = 'res.partner' AND ttype = 'many2one'
        )
        WHERE name = 'payment_type_customer'
        AND value_reference ~ %(old_pattern)s""", {
            'old_pattern': r"^payment.type,[ ]*([0-9]*)",
            'new_pattern': r"account.payment.mode,\1",
        }
    )

    # Copy mandate_id to account_move_line
    sql = """
    UPDATE account_move_line aml
    SET payment_mode_id = ai.payment_mode_id
    FROM account_invoice ai
    WHERE ai.id=aml.invoice_id
    AND aml.invoice_id IS NOT NULL
    AND ai.payment_mode_id IS NOT NULL;
    """
    openupgrade.logged_query(env.cr, sql)
