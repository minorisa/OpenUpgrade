# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenUpgrade module for Odoo
#    @copyright 2014-Today: Odoo Community Association
#    @author: Sylvain LE GAL <https://twitter.com/legalsylvain>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.openupgrade import openupgrade
from openerp.addons.openupgrade_records.lib import apriori

xml_ids = [
    ('portal.group_anonymous', 'base.group_public'),
    ('portal.group_portal', 'base.group_portal'),
    ('l10n_gt.GTQ', 'base.GTQ'),
    ('l10n_gt.rateGTQ', 'base.rateGTQ'),
]

unused_modules_70 = [
    'avanzosc_product_customerinfo',
    'it',
    'min_account',
    'min_account_analytic',
    'min_account_asset',
    'min_account_confirming',
    'min_account_import',
    'min_account_ini6',
    'min_account_menu',
    'min_account_payment',
    'min_account_payment_file_sepa',
    'min_account_periodical_invoicing',
    'min_account_report',
    'min_account_tax',
    'min_es_aeat_mod347',
    'min_facturae',
    'min_gtin',
    'min_invoice_picking',
    'min_last_purchase_product',
    'min_merge_purchase_order',
    'min_mrp_product_cost_calculation',
    'min_pdf',
    'min_product_bundle',
    'min_product_product',
    'min_q43',
    'min_sepa',
    'min_stock_diari',
    'min_stock_invoice',
    'min_summary_accounting_entries',
    'min_summary_ accounting_entries',
    'min_tg_pos_enhanced',
    'min_tpv_millores',
    'min_contract_billing',
    'min_minorisa',
    'min_project_erp',
    'min_project_issue',
    'send_invoices_by_mail',
    'l10n_cat_account',
    'l10n_cat_partner_data',
    'l10n_cat_toponyms',
    'l10n_es_account',
    'l10n_es_account_asset',
    'l10n_es_account_balance_report',
    'l10n_es_account_invoice_sequence',
    'l10n_es_account_invoice_sequence_fix',
    'l10n_es_aeat',
    'l10n_es_aeat_mod130',
    'l10n_es_aeat_mod303',
    'l10n_es_aeat_mod340',
    'l10n_es_aeat_mod340_type0',
    'l10n_es_aeat_mod347',
    'l10n_es_aeat_mod349',
    'l10n_es_auto_fiscal_position',
    'l10n_es_bank_statement',
    'l10n_es_facturae',
    'l10n_es_fiscal_year_closing',
    'l10n_es_gestion_comercial',
    'l10n_es_hr_nominas',
    'l10n_es_igic',
    'l10n_es_lopd',
    'l10n_es_partner',
    'l10n_es_partner_data',
    'l10n_es_partner_mercantil',
    'l10n_es_partner_seq',
    'l10n_es_payment_order',
    'l10n_es_prev_tesoreria',
    'l10n_es_pyme_account',
    'l10n_es_toponyms',
    'l10n_es_toponyms_region',
]


def cleanup_modules(cr):
    """Don't report as missing these modules, as they are integrated in
    other modules."""
    openupgrade.update_module_names(
        cr, [
            # from OCA/product-attribute
            ('product_customer_code', 'product_supplierinfo_for_customer'),
            # from OCA/sale-workflow - included in core
            ('sale_multi_picking', 'sale_procurement_group_by_line'),
            # from OCA/stock-logistics-workflow
            ('stock_cancel', 'stock_picking_back2draft'),
        ], merge_modules=True,
    )


def clean_write_uids(cr):
    """Some records are missing proper user IDs in write_uid due to a
    poor legacy Pentaho import from 5.0"""
    cr.execute("SELECT table_name FROM information_schema.columns "
               "WHERE table_schema='public' AND column_name='create_uid'")
    tables = cr.fetchall()
    for table in tables:
        cr.execute("""
        UPDATE %s SET write_uid = 1
        WHERE write_uid NOT IN (
            SELECT id FROM res_users
            )
        """ % table[0])
        cr.execute("""
        UPDATE %s SET create_uid = 1
        WHERE create_uid NOT IN (
            SELECT id FROM res_users
            )
        """ % table[0])


def remove_unused_views(cr):
    for module in unused_modules_70:
        cr.execute("""
            DELETE FROM ir_ui_view WHERE id IN 
                (SELECT res_id FROM ir_model_data 
                    WHERE model = 'ir.ui.view' AND module = '%s')
        """ % module)


def mark_unused_modules_uninstalled(cr):
    for module in unused_modules_70:
        cr.execute("""
        UPDATE ir_module_module SET state = 'uninstalled' WHERE name = '%s'
        """ % module)


@openupgrade.migrate()
def migrate(cr, version):
    # Drop view that inhibits changing field types. It will be recreated BTW
    cr.execute('drop view if exists report_document_user cascade')

    openupgrade.update_module_names(
        cr, apriori.renamed_modules.iteritems()
    )
    openupgrade.rename_xmlids(cr, xml_ids)
    openupgrade.check_values_selection_field(
        cr, 'ir_act_report_xml', 'report_type',
        ['controller', 'pdf', 'qweb-html', 'qweb-pdf', 'sxw', 'webkit'])
    openupgrade.check_values_selection_field(
        cr, 'ir_ui_view', 'type', [
            'calendar', 'diagram', 'form', 'gantt', 'graph', 'kanban',
            'qweb', 'search', 'tree'])

    # The tables stock.picking.in and stock.picking.out are merged into
    # stock.picking
    openupgrade.logged_query(
        cr, """
        UPDATE ir_attachment
        SET res_model = 'stock.picking'
        WHERE res_model in ('stock.picking.in', 'stock.picking.out');
        """)

    # Product.template is used for non variant product in v7 this was
    # product.product
    openupgrade.logged_query(
        cr, """
        UPDATE ir_attachment
        SET res_model = 'product.template'
        WHERE res_model = 'product.product';
        """)

    cleanup_modules(cr)
    clean_write_uids(cr)
    # remove_unused_views(cr)
    # mark_unused_modules_uninstalled(cr)
