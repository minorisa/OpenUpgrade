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

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(cr, version):
    # Drop view that inhibits changing field types. It will be recreated BTW
    cr.execute('drop view if exists analytic_entries_report cascade')

    # Minorisa
    # Create table analytic_account_tag for 11.0
    openupgrade.logged_query(
        cr,
        """
CREATE SEQUENCE public.account_analytic_tag_id_seq;

CREATE TABLE IF NOT EXISTS public.account_analytic_tag
    (
    id integer NOT NULL DEFAULT nextval('account_analytic_tag_id_seq'::regclass),
    name character varying COLLATE pg_catalog."default" NOT NULL,
    color integer,
    active boolean,
    create_uid integer,
    create_date timestamp without time zone,
    write_uid integer,
    write_date timestamp without time zone,
    CONSTRAINT account_analytic_tag_pkey PRIMARY KEY (id),
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

-- Index: account_analytic_tag_name_index

-- DROP INDEX public.account_analytic_tag_name_index;

CREATE INDEX account_analytic_tag_name_index
    ON public.account_analytic_tag USING btree
    (name COLLATE pg_catalog."default")
    TABLESPACE pg_default;
        """
    )
    # Insertar valors a account_analytic tag
    openupgrade.logged_query(
        cr,
        """
INSERT INTO public.account_analytic_tag (
    SELECT id, name, 10, true, create_uid, create_date, write_uid, write_date
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
