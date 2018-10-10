# -*- encoding: utf-8 -*-
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.logged_query(
        env.cr, """
        UPDATE stock_picking SET batch_id = legacy_batch_id
        """
    )
