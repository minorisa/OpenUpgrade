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

import logging
from openerp import pooler, SUPERUSER_ID
from openerp.openupgrade import openupgrade
logger = logging.getLogger('OpenUpgrade')


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
    # 'l10n_es_account',
    # 'l10n_es_account_asset',
    # 'l10n_es_account_balance_report',
    # 'l10n_es_account_invoice_sequence',
    # 'l10n_es_account_invoice_sequence_fix',
    # 'l10n_es_aeat',
    # 'l10n_es_aeat_mod130',
    # 'l10n_es_aeat_mod303',
    # 'l10n_es_aeat_mod340',
    # 'l10n_es_aeat_mod340_type0',
    # 'l10n_es_aeat_mod347',
    # 'l10n_es_aeat_mod349',
    # 'l10n_es_auto_fiscal_position',
    # 'l10n_es_bank_statement',
    # 'l10n_es_facturae',
    # 'l10n_es_fiscal_year_closing',
    # 'l10n_es_gestion_comercial',
    # 'l10n_es_hr_nominas',
    # 'l10n_es_igic',
    # 'l10n_es_lopd',
    # 'l10n_es_partner',
    # 'l10n_es_partner_data',
    # 'l10n_es_partner_mercantil',
    # 'l10n_es_partner_seq',
    # 'l10n_es_payment_order',
    # 'l10n_es_prev_tesoreria',
    # 'l10n_es_pyme_account',
    # 'l10n_es_toponyms',
    # 'l10n_es_toponyms_region',
]


def remove_custom_modules(cr, pool):
    mdobj = pool['ir.model.data']
    mdobj._module_data_uninstall(cr, SUPERUSER_ID, unused_modules_70)


def check_ir_actions_server_state(cr, pool):
    """Test if 'state' values are correct.
    If not, log an error to indicate that the user has to overload _get_state
    function in his custom modules."""
    ias_obj = pool['ir.actions.server']
    valid_selection = ias_obj._get_states(cr, SUPERUSER_ID)
    valid_list = [x[0] for x in valid_selection]
    ias_ids = ias_obj.search(
        cr, SUPERUSER_ID, [('state', 'not in', valid_list)])
    for ias in ias_obj.browse(cr, SUPERUSER_ID, ias_ids):
        logger.error(
            "Invalid value '%s' in the model 'ir_actions_server' "
            "for the field 'state'. (id %s).Please overload the new "
            "ir_actions_server._get_state function." % (
                ias.state, ias.id))


@openupgrade.migrate()
def migrate(cr, version):
    pool = pooler.get_pool(cr.dbname)
    remove_custom_modules(cr, pool)
