# -*- coding: utf-8 -*-
# Copyright (c) 2017 MINORISA <ramon.guiu@minorisa.net> 
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import _, api, fields, models
from openerp.models import expression

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    simplified_invoice = fields.Boolean('Simplified invoice', default=False,copy=False)
    
    
    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        
        res= super(AccountInvoice,self).onchange_partner_id(type,partner_id,date_invoice,payment_term,partner_bank_id,company_id)
        
        if partner_id:
            p = self.env['res.partner'].browse(partner_id or False)
            res['value']['simplified_invoice'] = p.simplified_invoice

        return res
    
    @api.multi
    def _sii_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self.accounting_date)
        currency = self.currency_id.with_context(date=invoice_date or fields.Date.context_today(self))
        if not self.partner_id.vat and self.simplified_invoice and currency.compute(self.amount_total,self.company_id.currency_id)< 400:
            raise exceptions.Warning(
                _("The partner has not a VAT configured.")
            )
        if not self.company_id.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if not self.company_id.sii_enabled:
            raise exceptions.Warning(
                _("This company doesn't have SII enabled.")
            )
        if not self.sii_enabled:
            raise exceptions.Warning(
                _("This invoice is not SII enabled.")
            )
    
    @api.multi
    def _get_sii_invoice_dict(self):
        invoice_date = self._change_date_format(self.accounting_date)
        company = self.company_id
        currency = self.currency_id.with_context(date=invoice_date or fields.Date.context_today(self))

#         if self.type in ('out_invoice','out_refund'):
#             ##TODO
#             currency = self.currency_id.with_context(date=invoice_date or fields.Date.context_today(self))
#             if not self.partner_id.vat and self.simplified_invoice and currency.compute(self.amount_total,self.company_id.currency_id)< 400:
#                 self.partner_id.write({'vat':'ESA00000000'})
#             ###    


        res = super(AccountInvoice,self)._get_sii_invoice_dict()  

        if self.type in ('out_invoice','out_refund'):
  
            if self.simplified_invoice and currency.compute(self.amount_total,self.company_id.currency_id)< 400:
                ##TODO
                self.partner_id.write({'vat':False})
                ###
                if 'Contraparte' in res['FacturaExpedida']:
                    del res['FacturaExpedida']['Contraparte']
                if 'TipoFactura' in res['FacturaExpedida']:
                    if res['FacturaExpedida']['TipoFactura'] == 'F1':
                        res['FacturaExpedida']['TipoFactura'] = 'F2'
                    else:
                        res['FacturaExpedida']['TipoFactura'] = 'R5'

        return res
