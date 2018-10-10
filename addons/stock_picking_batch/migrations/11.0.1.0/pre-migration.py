# -*- encoding: utf-8 -*-

from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    openupgrade.logged_query(
        cr, """
        ALTER TABLE stock_picking ADD legacy_batch_id INTEGER
        """
    )
    openupgrade.logged_query(
        cr, """
        UPDATE stock_picking 
        SET legacy_batch_id = wave_id, wave_id = null
        """
    )
