# -*- coding: utf-8 -*-
# Copyright (c) 2017 MINORISA <ramon.guiu@minorisa.net> 
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import _, api, fields, models
from openerp.models import expression

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    simplified_invoice = fields.Boolean('Simplified invoices', default=False,copy=False)