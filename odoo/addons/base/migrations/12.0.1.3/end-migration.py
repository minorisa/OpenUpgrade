# © 2018 Opener B.V. (stefan@opener.amsterdam)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openupgradelib import openupgrade, openupgrade_merge_records
from datetime import date

_logger = logging.getLogger(__name__)


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


def migrate_bu_auxiliary(env):
    # BU -> Etiquetes analitiques
    # TA/NA -> Grup i compte analitic

    oaag = env["account.analytic.group"]
    oaat = env["account.analytic.tag"]
    oaaa = env["account.analytic.account"]
    oaal = env["account.analytic.line"]
    oail = env["account.invoice.line"]

    # account_unitat_negoci
    env.cr.execute("""
    SELECT id, name, company_id
    FROM account_unitat_negoci
    """)
    map_bu = {}
    for line in env.cr.dictfetchall():
        bu = oaat.create({
            "name": line.get("name") or "GENERAL",
            "company_id": line.get("company_id"),
        })
        map_bu[line.get("id")] = bu.id

    # account_tipus_auxiliar
    env.cr.execute("""
    SELECT id, name, company_id
    FROM account_tipus_auxiliar
    """)
    map_ta = {}
    for line in env.cr.dictfetchall():
        ta = oaag.create({
            "name": line.get("name") or "GENERAL",
            "company_id": line.get("company_id"),
        })
        map_ta[line.get("id")] = ta.id

    # account_numero_auxiliar
    env.cr.execute("""
    SELECT id, tipus_auxiliar_id, name, company_id
    FROM account_numero_auxiliar
    """)
    map_na = {}
    for line in env.cr.dictfetchall():
        na = oaaa.create({
            "code": line.get("name") or "GENERAL",
            "name": line.get("name") or "GENERAL",
            "company_id": line.get("company_id"),
            "group_id": map_ta[line.get("tipus_auxiliar_id")]
        })
        map_na[line.get("id")] = na.id

    # Create analytic lines & update invoice lines
    env.cr.execute("""
    SELECT
        aml.id AS aml_id,
        aml.name AS aml_name,
        aml.date AS aml_date,
        ROUND(COALESCE(aml.debit, 0) - COALESCE(aml.credit, 0), 2) AS aml_amount,
        aml.ref AS aml_ref,
        aml.account_id AS aml_account_id,
        aml.partner_id AS aml_partner_id,
        aml.numero_auxiliar_id AS aml_numero_auxiliar_id,
        aml.unitat_negoci_id AS aml_unitat_negoci_id,
        aml.move_id AS aml_move_id,
        ail.product_id AS ail_product_id,
        ail.uom_id AS ail_uom_id
    FROM account_move_line aml
        LEFT JOIN account_invoice_line ail ON aml.move_id = ail.id
    WHERE aml.numero_auxiliar_id IS NOT NULL or aml.unitat_negoci_id IS NOT NULL
    """)
    for aml in env.cr.dictfetchall():
        # _logger.info(aml)
        # create analytic line
        un = map_bu.get(aml.get("aml_unitat_negoci_id"))
        na = map_na.get(aml.get("aml_numero_auxiliar_id"))
        if na:
            oaal.create({
                "name": aml.get("aml_name") or " ",
                "date": aml.get("aml_date"),
                "account_id": na,
                "amount": aml.get("aml_amount"),
                "ref": aml.get("aml_ref"),
                "general_account_id": aml.get("aml_account_id"),
                "move_id": aml.get("aml_id"),
                "product_id": aml.get("ail_product_id"),
                "product_uom_id": aml.get("ail_product_uom_id"),
                "tag_ids": [(4, un)] if un else [],
            })
            env.cr.execute("""
            UPDATE account_move_line
            SET analytic_account_id = %s
            WHERE id = %s
            """, (
                na,
                aml.get("aml_id"),
            ))
        if un:
            env.cr.execute("""
            INSERT INTO account_analytic_tag_account_move_line_rel
            (account_move_line_id, account_analytic_tag_id)
            VALUES (%s, %s)
            """, (
                aml.get("aml_id"),
                un,
            ))

    env.cr.execute("""
    SELECT id, unitat_negoci_id, numero_auxiliar_id
    FROM account_invoice_line
    WHERE unitat_negoci_id IS NOT NULL or numero_auxiliar_id IS NOT NULL
    """)
    for line in env.cr.dictfetchall():
        if line.get("unitat_negoci_id"):
            env.cr.execute("""
            INSERT INTO account_analytic_tag_account_invoice_line_rel
            (account_invoice_line_id, account_analytic_tag_id)
            VALUES (%s, %s)
            """, (
                line.get("id"),
                map_bu.get(line.get("unitat_negoci_id"))
            ))
        if line.get("numero_auxiliar_id"):
            env.cr.execute("""
            UPDATE account_invoice_line
            SET account_analytic_id = %s
            WHERE id = %s
            """, (
                map_na.get(line.get("numero_auxiliar_id")),
                line.get("id"),
            ))


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
        migrate_bu_auxiliary(env)
