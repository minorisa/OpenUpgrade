# -*- coding: utf-8 -*-
##############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(cr, version):
    # Drop view that inhibits changing field types. It will be recreated BTW
    cr.execute('drop view if exists analytic_entries_report cascade')

    # Minorisa
    # Create table account_analytic_tag for 11.0
    openupgrade.logged_query(
        cr,
        """
CREATE SEQUENCE public.account_analytic_tag_id_seq;

CREATE TABLE public.account_analytic_tag
(
    id integer NOT NULL DEFAULT nextval('account_analytic_tag_id_seq'::regclass),
    name character varying COLLATE pg_catalog."default" NOT NULL,
    color integer,
    active boolean,
    create_uid integer,
    create_date timestamp without time zone,
    write_uid integer,
    write_date timestamp without time zone,
    legacy_aux_id integer,
    analytic_dimension_id integer,
    CONSTRAINT account_analytic_tag_pkey PRIMARY KEY (id),
    CONSTRAINT account_analytic_tag_analytic_dimension_id_fkey FOREIGN KEY (analytic_dimension_id)
        REFERENCES public.account_analytic_dimension (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE SET NULL,
    CONSTRAINT account_analytic_tag_create_uid_fkey FOREIGN KEY (create_uid)
        REFERENCES public.res_users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE SET NULL,
    CONSTRAINT account_analytic_tag_write_uid_fkey FOREIGN KEY (write_uid)
        REFERENCES public.res_users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE SET NULL
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

COMMENT ON TABLE public.account_analytic_tag
    IS 'Analytic Tags';

COMMENT ON COLUMN public.account_analytic_tag.name
    IS 'Analytic Tag';

COMMENT ON COLUMN public.account_analytic_tag.color
    IS 'Color Index';

COMMENT ON COLUMN public.account_analytic_tag.active
    IS 'Active';

COMMENT ON COLUMN public.account_analytic_tag.create_uid
    IS 'Created by';

COMMENT ON COLUMN public.account_analytic_tag.create_date
    IS 'Created on';

COMMENT ON COLUMN public.account_analytic_tag.write_uid
    IS 'Last Updated by';

COMMENT ON COLUMN public.account_analytic_tag.write_date
    IS 'Last Updated on';

COMMENT ON COLUMN public.account_analytic_tag.analytic_dimension_id
    IS 'Dimension';

-- Index: account_analytic_tag_name_index

-- DROP INDEX public.account_analytic_tag_name_index;

CREATE INDEX account_analytic_tag_name_index
    ON public.account_analytic_tag USING btree
    (name COLLATE pg_catalog."default")
    TABLESPACE pg_default;        """
    )

    # Insertar BUs a account_analytic tag
    openupgrade.logged_query(
        cr,
        """
INSERT INTO public.account_analytic_tag (
    SELECT id, name, 1, true, 1, current_date, 1, current_date, id
    FROM public.account_unitat_negoci
    )
        """
    )
    # Update sequence
    openupgrade.logged_query(
        cr,
        """SELECT setval('public.account_analytic_tag_id_seq', 
            (SELECT MAX(id) FROM public.account_analytic_tag) + 1)"""
    )

    # Create m2m relation in account.move.line defined in 11.0
    openupgrade.logged_query(
        cr,
        """
CREATE TABLE public.account_analytic_tag_account_move_line_rel
(
    account_move_line_id integer NOT NULL,
    account_analytic_tag_id integer NOT NULL,
    CONSTRAINT account_analytic_tag_account__account_move_line_id_account__key UNIQUE (account_move_line_id, account_analytic_tag_id)
,
    CONSTRAINT account_analytic_tag_account_move__account_analytic_tag_id_fkey FOREIGN KEY (account_analytic_tag_id)
        REFERENCES public.account_analytic_tag (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT account_analytic_tag_account_move_lin_account_move_line_id_fkey FOREIGN KEY (account_move_line_id)
        REFERENCES public.account_move_line (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

COMMENT ON TABLE public.account_analytic_tag_account_move_line_rel
    IS 'RELATION BETWEEN account_move_line AND account_analytic_tag';

CREATE INDEX account_analytic_tag_account_move_l_account_analytic_tag_id_idx
    ON public.account_analytic_tag_account_move_line_rel USING btree
    (account_analytic_tag_id)
    TABLESPACE pg_default;

CREATE INDEX account_analytic_tag_account_move_line_account_move_line_id_idx
    ON public.account_analytic_tag_account_move_line_rel USING btree
    (account_move_line_id)
    TABLESPACE pg_default;
        """
    )
    # Insert existing unitats de negoci in this new relation
    openupgrade.logged_query(
        cr,
        """
INSERT INTO public.account_analytic_tag_account_move_line_rel (
    SELECT id, unitat_negoci_id
    FROM account_move_line
    WHERE unitat_negoci_id IS NOT null
    )         
        """
    )

    # Create m2m relation in account.invoice.line defined in 11.0
    openupgrade.logged_query(
        cr,
        """
CREATE TABLE public.account_analytic_tag_account_invoice_line_rel
(
    account_invoice_line_id integer NOT NULL,
    account_analytic_tag_id integer NOT NULL,
    CONSTRAINT account_analytic_tag_account__account_invoice_line_id_accou_key UNIQUE (account_invoice_line_id, account_analytic_tag_id)
,
    CONSTRAINT account_analytic_tag_account_invoi_account_analytic_tag_id_fkey FOREIGN KEY (account_analytic_tag_id)
        REFERENCES public.account_analytic_tag (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT account_analytic_tag_account_invoi_account_invoice_line_id_fkey FOREIGN KEY (account_invoice_line_id)
        REFERENCES public.account_invoice_line (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

COMMENT ON TABLE public.account_analytic_tag_account_invoice_line_rel
    IS 'RELATION BETWEEN account_invoice_line AND account_analytic_tag';

CREATE INDEX account_analytic_tag_account_invoic_account_analytic_tag_id_idx
    ON public.account_analytic_tag_account_invoice_line_rel USING btree
    (account_analytic_tag_id)
    TABLESPACE pg_default;

CREATE INDEX account_analytic_tag_account_invoic_account_invoice_line_id_idx
    ON public.account_analytic_tag_account_invoice_line_rel USING btree
    (account_invoice_line_id)
    TABLESPACE pg_default;
        """
    )
    # Insert records in new relation
    openupgrade.logged_query(
        cr,
        """
INSERT INTO public.account_analytic_tag_account_invoice_line_rel (
    SELECT id, unitat_negoci_id
    FROM account_invoice_line
    WHERE unitat_negoci_id IS NOT null
)        
        """
    )

    # =============================
    # Account Tipus Auxiliar

    # Get max id in account_analytic_tag
    cr.execute("SELECT MAX(id) FROM public.account_analytic_tag")
    max_id = cr.fetchone()[0] or 1000
    max_id += 1

    # Get tipus auxiliars -> dimensions
    cr.execute("SELECT * FROM account_numero_auxiliar")
    numero_auxs = cr.dictfetchall()
    xtagid = max_id
    for aux in numero_auxs:
        _logger.info(aux)
        cr.execute(
                """
INSERT INTO public.account_analytic_tag  VALUES (
    %(new_id)s, '%(xname)s', 2, true, 1, current_date, 1, 
        current_date, %(auxid)s
    );
                """ % {
                    'new_id': xtagid,
                    'xname': aux['name'],
                    'auxid': aux['id'],
                }
            )
        xtagid += 1

    # Update tag_ids in account_invoice_line
    openupgrade.logged_query(
        cr,
        """
INSERT INTO public.account_analytic_tag_account_invoice_line_rel (
    SELECT ail.id, aat.id 
    FROM account_invoice_line ail 
    LEFT JOIN account_analytic_tag aat ON ail.numero_auxiliar_id = aat.legacy_aux_id
    WHERE ail.numero_auxiliar_id IS NOT null
    )        
        """
    )

    # Update tag_ids in account_move_line
    openupgrade.logged_query(
        cr,
        """
INSERT INTO public.account_analytic_tag_account_move_line_rel (
    SELECT aml.id, aat.id 
    FROM account_move_line aml 
    LEFT JOIN account_analytic_tag aat ON aml.numero_auxiliar_id = aat.legacy_aux_id
    WHERE aml.numero_auxiliar_id IS NOT null
    )        
        """
    )

    # Migrate periodical_invoicing

    openupgrade.rename_tables(cr, [
        ('account_periodical_invoicing_agreement',
         'account_pro_agreement'),
        ('account_periodical_invoicing_agreement_line',
         'account_pro_agreement_line'),
        ('account_periodical_invoicing_agreement_invoice',
         'account_pro_agreement_invoice'),
    ])
    openupgrade.logged_query(cr,"""
    ALTER TABLE account_pro_agreement ADD COLUMN currency_id INTEGER;
    UPDATE account_pro_agreement SET currency_id = 1;
    """)
    openupgrade.drop_columns(cr, [
        ('account_pro_agreement', 'unitat_negoci_id'),
        ('account_pro_agreement', 'billing_day'),
        ('account_pro_agreement_line', 'year'),
    ])
    openupgrade.rename_columns(cr, {
        'account_pro_agreement_line': [
            ('account_analytic_id', 'analytic_id'),
            ('preu_compra', 'purchase_price'),
        ]
    })

    # Create m2m relation between agreement line and analytic tag
    openupgrade.logged_query(cr, """
CREATE TABLE public.account_analytic_tag_account_pro_agreement_line_rel
(
    account_pro_agreement_line_id integer NOT NULL,
    account_analytic_tag_id integer NOT NULL,
    CONSTRAINT account_analytic_tag_account__account_pro_agreement_line_id_key UNIQUE (account_pro_agreement_line_id, account_analytic_tag_id)
,
    CONSTRAINT account_analytic_tag_account__account_pro_agreement_line_i_fkey FOREIGN KEY (account_pro_agreement_line_id)
        REFERENCES public.account_pro_agreement_line (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT account_analytic_tag_account_pro_a_account_analytic_tag_id_fkey FOREIGN KEY (account_analytic_tag_id)
        REFERENCES public.account_analytic_tag (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

COMMENT ON TABLE public.account_analytic_tag_account_pro_agreement_line_rel
    IS 'RELATION BETWEEN account_pro_agreement_line AND account_analytic_tag';

CREATE INDEX account_analytic_tag_account__account_pro_agreement_line_id_idx
    ON public.account_analytic_tag_account_pro_agreement_line_rel USING btree
    (account_pro_agreement_line_id)
    TABLESPACE pg_default;

CREATE INDEX account_analytic_tag_account_pro_ag_account_analytic_tag_id_idx
    ON public.account_analytic_tag_account_pro_agreement_line_rel USING btree
    (account_analytic_tag_id)
    TABLESPACE pg_default;    
    """)

    # Insert BU tags in m2m
    openupgrade.logged_query(cr, """
INSERT INTO public.account_analytic_tag_account_pro_agreement_line_rel (
    SELECT id, unitat_negoci_id
    FROM account_pro_agreement_line
    WHERE unitat_negoci_id IS NOT null
    )    
    """)
