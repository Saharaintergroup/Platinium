# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):

    _inherit = "pos.payment.method"

    cash_journal_id = fields.Many2one('account.journal', domain=[
                                      ('type', 'in', ('bank', 'cash'))])
    is_cash_count = fields.Boolean(default=True, readonly=False)

# class PriceListInherit(models.Model):
#     _inherit = 'pos.config'
#
#     @api.constrains('pricelist_id', 'use_pricelist', 'available_pricelist_ids', 'journal_id', 'invoice_journal_id',
#                     'payment_method_ids')
#     def _check_currencies(self):
#         for config in self:
#             if config.use_pricelist and config.pricelist_id not in config.available_pricelist_ids:
#                 raise ValidationError(_("The default pricelist must be included in the available pricelists."))
#         # if any(self.available_pricelist_ids.mapped(lambda pricelist: pricelist.currency_id != self.currency_id)):
#         #     raise ValidationError(_("All available pricelists must be in the same currency as the company or"
#         #                             " as the Sales Journal set on this point of sale if you use"
#         #                             " the Accounting application."))
#         if self.invoice_journal_id.currency_id and self.invoice_journal_id.currency_id != self.currency_id:
#             raise ValidationError(_(
#                 "The invoice journal must be in the same currency as the Sales Journal or the company currency if that is not set."))
#         if any(
#                 self.payment_method_ids \
#                         .filtered(lambda pm: pm.is_cash_count) \
#                         .mapped(
#                     lambda pm: self.currency_id not in (self.company_id.currency_id | pm.cash_journal_id.currency_id))
#         ):
#             raise ValidationError(_(
#                 "All payment methods must be in the same currency as the Sales Journal or the company currency if that is not set."))
#
#
#




