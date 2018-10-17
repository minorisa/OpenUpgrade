# -*- encoding: utf-8 -*-

from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(env, version):
    # Minorisa
    # Convert User IDs in Employee IDs in account.analytic.line
    openupgrade.logged_query(
        env.cr, """
        UPDATE account_analytic_line SET employee_id = hr_employee.id
        FROM hr_employee, resource_resource
        WHERE hr_employee.resource_id = resource_resource.id
        AND account_analytic_line.user_id = resource_resource.user_id
        """
    )
