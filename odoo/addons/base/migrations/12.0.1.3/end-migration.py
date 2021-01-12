# © 2018 Opener B.V. (stefan@opener.amsterdam)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade, openupgrade_merge_records


def update_model_terms_translations(env):
    """ Adapt to changes in https://github.com/odoo/odoo/pull/26925, that
    introduces a separate translation type for xml structured fields. First,
    deduplicate existing model translations with new model_terms translations
    that were loaded during the migration. """
    openupgrade.logged_query(
        env.cr, """ DELETE FROM ir_translation WHERE id IN (
        SELECT it2.id FROM ir_translation it1
        JOIN ir_translation it2 ON it1.type in ('model', 'model_terms')
            AND it2.type in ('model', 'model_terms')
            AND it1.name = it2.name
            AND it1.res_id = it2.res_id
            AND it1.lang = it2.lang
            AND it1.id < it2.id); """)
    names = []
    for rec in env['ir.model.fields'].search([('translate', '=', True)]):
        try:
            field = env[rec.model]._fields[rec.name]
        except KeyError:
            continue
        if callable(field.translate):
            names.append('%s,%s' % (rec.model, rec.name))
    if names:
        openupgrade.logged_query(
            env.cr,
            """ UPDATE ir_translation
            SET type = 'model_terms'
            WHERE type = 'model' AND name IN %s """,
            (tuple(names),))


def fork_off_system_user(env):
    """ Fork user admin off from user system. User admin keeps the original
    partner, and user system gets a new partner. """
    user_root = env.ref('base.user_root')
    partner_admin = env.ref('base.partner_admin')
    partner_root = env.ref('base.partner_admin').copy({'name': 'System'})
    login = user_root.login
    user_root.login = '__system__'
    user_admin = env.ref('base.user_root').copy({
        'partner_id': partner_admin.id,
        'login': login,
    })
    # copy old passwords for not losing them on new admin user
    crypt = openupgrade.column_exists(env.cr, 'res_users', 'password_crypt')
    set_query = "SET password = ru2.password "
    if crypt:
        set_query += ", password_crypt = ru2.password_crypt "
    env.cr.execute(
        "UPDATE res_users ru " + set_query +
        "FROM res_users ru2 WHERE ru2.id = %s AND ru.id = %s",
        (user_root.id, user_admin.id),
    )
    user_root.write({
        'partner_id': partner_root.id,
        'email': partner_admin.email,
    })
    partner_admin.email = 'root@example.com'
    env.cr.execute(
        """ UPDATE ir_model_data SET res_id = %s
        WHERE module = 'base' AND name = 'user_admin'""", (user_admin.id,))
    env.cr.execute(
        """ UPDATE ir_model_data SET res_id = %s
        WHERE module = 'base' AND name = 'partner_root'""", (partner_root.id,))
    openupgrade.logged_query(
        env.cr,
        """ UPDATE ir_model_data SET res_id = %(user_admin)s
        WHERE model = 'res.users' AND res_id = %(user_root)s
        AND (module != 'base' OR name != 'user_root') """,
        {'user_admin': user_admin.id, 'user_root': user_root.id})
    # Get create_uid and write_uid columns to ignore
    env.cr.execute(
        """ SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = 'res_users' and ccu.column_name = 'id'
            AND kcu.column_name IN ('create_uid', 'write_uid')
        """)
    exclude_columns = env.cr.fetchall() + [
        ('ir_cron', 'user_id'), ('res_groups_users_rel', 'uid'),
        ('res_company_users_rel', 'user_id'),
    ]

    openupgrade_merge_records.merge_records(
        env, 'res.users', [user_root.id], user_admin.id,
        method='sql', delete=False, exclude_columns=exclude_columns)
    # Circumvent ORM when setting root user inactive, because
    # "You cannot deactivate the user you're currently logged in as."
    set_query = "SET active = FALSE, password = NULL"
    if crypt:
        set_query += ", password_crypt = NULL"
    env.cr.execute(
        "UPDATE res_users " + set_query + " WHERE id = %s",
        (user_root.id, ),
    )
    # Ensure also partner_root is inactive
    env.cr.execute(
        """ UPDATE res_partner
            SET active = FALSE WHERE id = %s """,
        (partner_root.id,))


def fill_res_users_password_from_password_crypt(cr):
    openupgrade.logged_query(
        cr,
        """UPDATE res_users
        SET password = password_crypt
        WHERE password_crypt IS NOT NULL
        """,
    )


def migrate_account_pro_agreement(cr):
    openupgrade.rename_tables(cr, [
        ('account_periodical_invoicing_agreement',
         'account_pro_agreement'),
        ('account_periodical_invoicing_agreement_invoice',
         'account_pro_agreement_invoice'),
        ('account_periodical_invoicing_agreement_line',
         'account_pro_agreement_line'),
        ('account_periodical_invoicing_agreement_renewal',
         'account_pro_agreement_renewal'),
    ])
    openupgrade.rename_columns(cr, {
        'account_pro_agreement_line': [
            ('account_analytic_id', 'analytic_id'),
            ('preu_compra', 'purchase_price'),
        ]
    })


def create_split_supplier_payment_modes(env):
    pmethod = env["account.payment.method"].search([
        ("payment_type", "=", "outbound")
    ], limit=1)
    partners = env["res.partner"].search([])
    try:
        modes = partners.mapped("supplier_payment_mode_id")
        mapping = {}
        for mode in modes:
            if mode:
                mapping[mode] = mode.copy({
                    "name": "[From Supplier Migration] " + mode.name,
                    "payment_method_id": pmethod.id,
                })
        for partner in env["res.partner"].search([
                    ("supplier_payment_mode_id", "!=", False)
                ]):
            partner.supplier_payment_mode_id = mapping[
                partner.supplier_payment_mode_id]
    except Exception:
        pass


def migrate_bu_auxiliary_aml(env):
    # account_move_line
    oaaa = env["account.analytic.account"]
    oaml = env["account.move.line"]
    env.cr.execute("""
    SELECT aml.id,
           aml.unitat_negoci_id,
           un.name AS un_name,
           un.code AS un_code,
           aml.numero_auxiliar_id,
           na.name AS na_name,
           na.code AS na_code,
           aml.tipus_auxiliar_id,
           ta.name AS ta_name,
           ta.code AS ta_code
    FROM account_move_line aml
        LEFT JOIN account_unitat_negoci un ON aml.unitat_negoci_id = un.id
        LEFT JOIN account_numero_auxiliar na ON aml.numero_auxiliar_id = na.id
        LEFT JOIN account_tipus_auxiliar ta ON aml.tipus_auxiliar_id = ta.id
    """)
    for aml in env.cr.dictfetchall():
        na = ta = un = None

        if aml.get('na_code'):
            na = oaaa.search([
                ('code', '=', aml.get('na_code')),
            ], limit=1)
            if not na:
                na = oaaa.create({
                    'name': aml.get('na_name'),
                    'code': aml.get('na_code'),
                })

        if aml.get('ta_code'):
            ta = oaaa.search([
                ('code', '=', aml.get('ta_code')),
            ], limit=1)
            if not ta:
                ta = oaaa.create({
                    'name': aml.get('ta_name'),
                    'code': aml.get('ta_code'),
                })
            if na and not na.parent_id:
                na.parent_id = ta

        if aml.get('un_code'):
            un = oaaa.search([
                ('code', '=', aml.get('un_code')),
            ], limit=1)
            if not un:
                un = oaaa.create({
                    'name': aml.get('un_name'),
                    'code': aml.get('un_code'),
                })
            if ta and not ta.parent_id:
                ta.parent_id = un

        move_line = oaml.browse(aml.get('id'))
        move_line.analytic_account_id = na or ta or un


def migrate_bu_auxiliary_ail(env):
    # account_invoice_line
    oaaa = env["account.analytic.account"]
    oail = env["account.invoice.line"]
    env.cr.execute("""
    SELECT ail.id,
           ail.unitat_negoci_id,
           un.name AS un_name,
           un.code AS un_code,
           ail.numero_auxiliar_id,
           na.name AS na_name,
           na.code AS na_code,
           ail.tipus_auxiliar_id,
           ta.name AS ta_name,
           ta.code AS ta_code
    FROM account_invoice_line ail
        LEFT JOIN account_unitat_negoci un ON ail.unitat_negoci_id = un.id
        LEFT JOIN account_numero_auxiliar na ON ail.numero_auxiliar_id = na.id
        LEFT JOIN account_tipus_auxiliar ta ON ail.tipus_auxiliar_id = ta.id
    """)
    for ail in env.cr.dictfetchall():
        na = ta = un = None

        if ail.get('na_code'):
            na = oaaa.search([
                ('code', '=', ail.get('na_code')),
            ], limit=1)
            if not na:
                na = oaaa.create({
                    'name': ail.get('na_name'),
                    'code': ail.get('na_code'),
                })

        if ail.get('ta_code'):
            ta = oaaa.search([
                ('code', '=', ail.get('ta_code')),
            ], limit=1)
            if not ta:
                ta = oaaa.create({
                    'name': ail.get('ta_name'),
                    'code': ail.get('ta_code'),
                })
            if na and not na.parent_id:
                na.parent_id = ta

        if ail.get('un_code'):
            un = oaaa.search([
                ('code', '=', ail.get('un_code')),
            ], limit=1)
            if not un:
                un = oaaa.create({
                    'name': ail.get('un_name'),
                    'code': ail.get('un_code'),
                })
            if ta and not ta.parent_id:
                ta.parent_id = un

        inv_line = oail.browse(ail.get('id'))
        inv_line.account_analytic_id = na or ta or un


def migrate_bu_auxiliary_aal(env):
    oaal = env["account.analytic.line"]
    amls = env["account.move.line"].search([
        ('analytic_account_id', '!=', False),
        '|',
        ('debit', '>', 0),
        ('credit', '>', 0),
    ])
    for aml in amls:
        oaal.create({
            'name': aml.name,
            'date': aml.date,
            'account_id': aml.analytic_account_id.id,
            'amount': round(aml.debit - aml.credit, 2),
            'ref': aml.ref,
            'general_account_id': aml.account_id.id,
        })


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.disable_invalid_filters(env)
    update_model_terms_translations(env)
    fork_off_system_user(env)
    if openupgrade.column_exists(env.cr, 'res_users', 'password_crypt'):
        fill_res_users_password_from_password_crypt(env.cr)

    if openupgrade.table_exists(
            env.cr, 'account_periodical_invoicing_agreement'):
        migrate_account_pro_agreement(env.cr)
    create_split_supplier_payment_modes(env)
    if openupgrade.table_exists(
            env.cr, 'account_unitat_negoci'):
        migrate_bu_auxiliary_aml(env)
        migrate_bu_auxiliary_ail(env)
        migrate_bu_auxiliary_aal(env)
