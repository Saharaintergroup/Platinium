# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT, defaultdict
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp


class PosOrder(models.Model):

    _inherit = "pos.order"

    require_customer = fields.Boolean(
        related='payment_ids.payment_method_id.require_customer',
    )

    @api.constrains('partner_id', 'session_id')
    def _check_partner(self):
        for rec in self:
            if rec.require_customer == True and not rec.partner_id:
                raise exceptions.ValidationError(_(
                    'Customer is required for this order and is missing.'))

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        """Create account.bank.statement.lines from the dictionary given to the parent function.

        If the payment_line is an updated version of an existing one, the existing payment_line will first be
        removed before making a new one.
        :param pos_order: dictionary representing the order.
        :type pos_order: dict.
        :param order: Order object the payment lines should belong to.
        :type order: pos.order
        :param pos_session: PoS session the order was created in.
        :type pos_session: pos.session
        :param draft: Indicate that the pos_order is not validated yet.
        :type draft: bool.
        """
        prec_acc = order.pricelist_id.currency_id.decimal_places
        order_bank_statement_lines = self.env['pos.payment'].search(
            [('pos_order_id', '=', order.id)])
        order_bank_statement_lines.unlink()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                order.add_payment(self._payment_fields(
                    order, payments[2], pos_order))

        order.amount_paid = sum(order.payment_ids.mapped('amount'))
        bank = self.env['res.bank'].browse(pos_order.get('bank_id'))
        partner = self.env['res.partner'].browse(pos_order.get('owner_name'))
        provider = self.env['payment.provider'].browse(
            pos_order.get('provider_name'))
        terminal = self.env['payment.provider'].browse(
            pos_order.get('terminal_name'))
        if not draft and not float_is_zero(pos_order['amount_return'], prec_acc):
            cash_payment_method = pos_session.payment_method_ids.filtered('is_cash_count')[
                :1]
            if not cash_payment_method:
                raise UserError(
                    _("No cash statement found for this session. Unable to record returned cash."))
            return_payment_vals = {
                'name': _('return'),
                'pos_order_id': order.id,
                'amount': -pos_order['amount_return'],
                'payment_date': fields.Date.context_today(self),
                'payment_method_id': cash_payment_method.id,
                'cheque_bank': bank.id,
                'bank_account': pos_order.get('bank_account'),
                'cheque_number': pos_order.get('cheque_number'),
                'cheque_owner_name': pos_order.get('owner_name'),
                'cardholder_name': pos_order.get('owner_name'),
                'payment_provider': provider.id,
                'payment_terminal': terminal.id
            }
            order.add_payment(return_payment_vals)

    def _payment_fields(self, order, ui_paymentline, pos_order):
        payment_date = ui_paymentline['name']
        bank = self.env['res.bank'].browse(pos_order.get('bank_id'))
        partner = self.env['res.partner'].browse(pos_order.get('owner_name'))
        provider = self.env['payment.provider'].browse(
            pos_order.get('provider_name'))
        terminal = self.env['payment.provider'].browse(
            pos_order.get('terminal_name'))
        payment_date = fields.Date.context_today(
            self, fields.Datetime.from_string(payment_date))
        payment_method = self.env['pos.payment.method'].browse(
            ui_paymentline['payment_method_id'])
        if payment_method.cheque_information == True:
            return {
                'amount': ui_paymentline['amount'] or 0.0,
                'payment_date': payment_date,
                'payment_method_id': ui_paymentline['payment_method_id'],
                'card_type': ui_paymentline['card_type'],
                'transaction_id': pos_order.get('cheque_number'),
                'pos_order_id': order.id,
                'cheque_owner_name': pos_order.get('owner_name'),
                'cardholder_name': pos_order.get('owner_name'),
                'cheque_bank': bank.id,
                'payment_provider': provider.id,
                'payment_terminal': terminal.id,
                'bank_account': pos_order.get('bank_account'),
                'cheque_number': pos_order.get('cheque_number'),
            }
        else:
            return {
                'amount': ui_paymentline['amount'] or 0.0,
                'payment_date': payment_date,
                'payment_method_id': ui_paymentline['payment_method_id'],
                'cardholder_name': ui_paymentline['cardholder_name'],
                'card_type': ui_paymentline.get('card_type'),
                'transaction_id': ui_paymentline.get('transaction_id'),
                'payment_provider': ui_paymentline.get('payment_provider'),
                'payment_terminal': ui_paymentline.get('payment_terminal'),
                'pos_order_id': order.id,
            }


class PosConfigInherit(models.Model):

    _inherit = "pos.config"

    cheque_information = fields.Boolean(string="Add Payment Details")
    bank = fields.Many2one('res.bank')
    # partner = fields.Many2one('res.partner')
    provider = fields.Many2one('payment.provider')
    terminal = fields.Many2one('payment.terminal')


class PosOrderInherit(models.Model):

    _inherit = "pos.payment"

    cheque_owner_name = fields.Char(string="Owner name")
    cheque_bank = fields.Many2one('res.bank', string="Bank")
    bank_account = fields.Char(string="Card Number")
    cheque_number = fields.Char(string="Payment Transaction ID")
    # cardholder_name = fields.Many2one('res.partner',string="Cardholder Name")
    payment_provider = fields.Many2one('payment.provider', "Payment Provider")
    payment_terminal = fields.Many2one('payment.terminal', "Payment Terminal")


class AccountJournal(models.Model):

    _inherit = "pos.payment.method"

    cheque_information = fields.Boolean(string="Second Currency")
    cash_journal_id = fields.Many2one('account.journal', domain=[
                                      ('type', 'in', ('bank', 'cash'))])
    is_cash_count = fields.Boolean(default=True, readonly=True)
    require_customer = fields.Boolean(
        string=' Require Customer', )
    currency_id = fields.Many2one('res.currency',"Currency")
    currency_rate = fields.Float("Currency Rate",related="currency_id.rate",digits=(5, 3))
    currency_symbol = fields.Char("Currency Symbol",related="currency_id.symbol")



class PaymentProvider(models.Model):
    _name = 'payment.provider'

    name = fields.Char("Payment Provider")


class PaymentTerminal(models.Model):
    _name = 'payment.terminal'

    name = fields.Char("Payment Terminal")
    payment_method_id = fields.Many2one('pos.payment.method', "Payment Method")
