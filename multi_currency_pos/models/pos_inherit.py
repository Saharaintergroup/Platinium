# -*- coding: utf-8 -*-
from functools import partial
from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT, defaultdict
import math

from odoo.addons.point_of_sale.models.pos_session import PosSession as PosSession



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
    currency_rate = fields.Float("Currency Rate",digits=(5, 1),compute="_get_currency_rate",store=True)
    currency_symbol = fields.Char("Currency Symbol",related="currency_id.symbol")

    @api.depends('currency_id.rate')
    def _get_currency_rate(self):
        for rec in self:
            amount_total = 0
            val = rec.currency_id.rate
            if (float(val) % 1) > 0.5:
                amount_total += math.ceil(val)
            elif (float(val) % 1) <= 0.5 and (float(val) % 1) > 0:
                print(float(val) % 1)
                amount_total += math.floor(val) + 0.5
            print("//////",amount_total)
            rec.currency_rate = amount_total





class PaymentProvider(models.Model):
    _name = 'payment.provider'

    name = fields.Char("Payment Provider")


class PaymentTerminal(models.Model):
    _name = 'payment.terminal'

    name = fields.Char("Payment Terminal")
    payment_method_id = fields.Many2one('pos.payment.method', "Payment Method")

class PosSessionInherit2(models.Model):
    _inherit = 'pos.session'


    def check_status(self):
        for rec in self:
            rec.write({'state': 'closed', 'stop_at': rec.start_at})
            return True



    def _accumulate_amounts(self, data):
        res = super(PosSessionInherit2, self)._accumulate_amounts(data)
        # Accumulate the amounts for each accounting lines group
        # Each dict maps `key` -> `amounts`, where `key` is the group key.
        # E.g. `combine_receivables` is derived from pos.payment records
        # in the self.order_ids with group key of the `payment_method_id`
        # field of the pos.payment record.
        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
        tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
        split_receivables = defaultdict(amounts)
        split_receivables_cash = defaultdict(amounts)
        combine_receivables = defaultdict(amounts)
        combine_receivables_cash = defaultdict(amounts)
        invoice_receivables = defaultdict(amounts)
        sales = defaultdict(amounts)
        taxes = defaultdict(tax_amounts)
        stock_expense = defaultdict(amounts)
        stock_return = defaultdict(amounts)
        stock_output = defaultdict(amounts)
        rounding_difference = {'amount': 0.0, 'amount_converted': 0.0}
        # Track the receivable lines of the invoiced orders' account moves for reconciliation
        # These receivable lines are reconciled to the corresponding invoice receivable lines
        # of this session's move_id.
        order_account_move_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        rounded_globally = self.company_id.tax_calculation_rounding_method == 'round_globally'
        for order in self.order_ids:
            # Combine pos receivable lines
            # Separate cash payments for cash reconciliation later.
            for payment in order.payment_ids:
                amount, date = payment.amount, payment.payment_date
                amount_currency = payment.payment_method_id.currency_rate
                if payment.payment_method_id.split_transactions:
                    if payment.payment_method_id.is_cash_count:
                        split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment], {'amount': amount}, date)
                    else:
                        split_receivables[payment] = self._update_amounts(split_receivables[payment], {'amount': amount}, date)
                else:
                    key = payment.payment_method_id
                    if payment.payment_method_id.is_cash_count and payment.payment_method_id.cheque_information:
                        combine_receivables_cash[key] = self._update_amounts(combine_receivables_cash[key], {'amount': amount*amount_currency}, date)
                    elif payment.payment_method_id.is_cash_count:
                        combine_receivables_cash[key] = self._update_amounts(combine_receivables_cash[key],
                                                                             {'amount': amount }, date)
                    else:
                        combine_receivables[key] = self._update_amounts(combine_receivables[key], {'amount': amount}, date)

            if order.is_invoiced:
                # Combine invoice receivable lines
                key = order.partner_id.property_account_receivable_id.id
                if self.config_id.cash_rounding:
                    invoice_receivables[key] = self._update_amounts(invoice_receivables[key], {'amount': order.amount_paid}, order.date_order)
                else:
                    invoice_receivables[key] = self._update_amounts(invoice_receivables[key], {'amount': order.amount_total}, order.date_order)
                # side loop to gather receivable lines by account for reconciliation
                for move_line in order.account_move.line_ids.filtered(lambda aml: aml.account_id.internal_type == 'receivable' and not aml.reconciled):
                    order_account_move_receivable_lines[move_line.account_id.id] |= move_line
            else:
                order_taxes = defaultdict(tax_amounts)
                for payment in order.payment_ids:
                    if payment.payment_method_id.cheque_information:
                        currency_rate = payment.payment_method_id.currency_rate
                        for order_line in order.lines:
                            line = self._prepare_line(order_line)
                            # Combine sales/refund lines
                            sale_key = (
                                # account
                                line['income_account_id'],
                                # sign
                                -1 if line['amount'] < 0 else 1,
                                # for taxes
                                tuple((tax['id'], tax['account_id'], tax['tax_repartition_line_id']) for tax in line['taxes']),
                            )
                            sales[sale_key] = self._update_amounts(sales[sale_key], {'amount': line['amount']*currency_rate}, line['date_order'])
                            # Combine tax lines
                            for tax in line['taxes']:
                                tax_key = (tax['account_id'], tax['tax_repartition_line_id'], tax['id'], tuple(tax['tag_ids']))
                                order_taxes[tax_key] = self._update_amounts(
                                    order_taxes[tax_key],
                                    {'amount': tax['amount'], 'base_amount': tax['base']},
                                    tax['date_order'],
                                    round=not rounded_globally
                                )
                    else:
                        for order_line in order.lines:
                            line = self._prepare_line(order_line)
                            # Combine sales/refund lines
                            sale_key = (
                                # account
                                line['income_account_id'],
                                # sign
                                -1 if line['amount'] < 0 else 1,
                                # for taxes
                                tuple((tax['id'], tax['account_id'], tax['tax_repartition_line_id']) for tax in line['taxes']),
                            )
                            sales[sale_key] = self._update_amounts(sales[sale_key], {'amount': line['amount']}, line['date_order'])
                            # Combine tax lines
                            for tax in line['taxes']:
                                tax_key = (tax['account_id'], tax['tax_repartition_line_id'], tax['id'], tuple(tax['tag_ids']))
                                order_taxes[tax_key] = self._update_amounts(
                                    order_taxes[tax_key],
                                    {'amount': tax['amount'], 'base_amount': tax['base']},
                                    tax['date_order'],
                                    round=not rounded_globally
                                )

                for tax_key, amounts in order_taxes.items():
                    if rounded_globally:
                        amounts = self._round_amounts(amounts)
                    for amount_key, amount in amounts.items():
                        taxes[tax_key][amount_key] += amount

                if self.company_id.anglo_saxon_accounting and order.picking_ids.ids:
                    # Combine stock lines
                    stock_moves = self.env['stock.move'].search([
                        ('picking_id', 'in', order.picking_ids.ids),
                        ('company_id.anglo_saxon_accounting', '=', True),
                        ('product_id.categ_id.property_valuation', '=', 'real_time')
                    ])
                    for move in stock_moves:
                        exp_key = move.product_id._get_product_accounts()['expense']
                        out_key = move.product_id.categ_id.property_stock_account_output_categ_id
                        amount = -sum(move.sudo().stock_valuation_layer_ids.mapped('value'))
                        stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                        if move.location_id.usage == 'customer':
                            stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                        else:
                            stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)

                if self.config_id.cash_rounding:
                    diff = order.amount_paid - order.amount_total
                    rounding_difference = self._update_amounts(rounding_difference, {'amount': diff}, order.date_order)

                # Increasing current partner's customer_rank
                order.partner_id._increase_rank('customer_rank')

        if self.company_id.anglo_saxon_accounting:
            global_session_pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
            if global_session_pickings:
                stock_moves = self.env['stock.move'].search([
                    ('picking_id', 'in', global_session_pickings.ids),
                    ('company_id.anglo_saxon_accounting', '=', True),
                    ('product_id.categ_id.property_valuation', '=', 'real_time'),
                ])
                for move in stock_moves:
                    exp_key = move.product_id._get_product_accounts()['expense']
                    out_key = move.product_id.categ_id.property_stock_account_output_categ_id
                    amount = -sum(move.stock_valuation_layer_ids.mapped('value'))
                    stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date)
                    if move.location_id.usage == 'customer':
                        stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date)
                    else:
                        stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date)
        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)

        data.update({
            'taxes':                               taxes,
            'sales':                               sales,
            'stock_expense':                       stock_expense,
            'split_receivables':                   split_receivables,
            'combine_receivables':                 combine_receivables,
            'split_receivables_cash':              split_receivables_cash,
            'combine_receivables_cash':            combine_receivables_cash,
            'invoice_receivables':                 invoice_receivables,
            'stock_return':                        stock_return,
            'stock_output':                        stock_output,
            'order_account_move_receivable_lines': order_account_move_receivable_lines,
            'rounding_difference':                 rounding_difference,
            'MoveLine':                            MoveLine
        })
        return res

    def _get_sale_vals(self, key, amount, amount_converted):
        account_id, sign, tax_keys = key
        tax_ids = set(tax[0] for tax in tax_keys)
        applied_taxes = self.env['account.tax'].browse(tax_ids)
        title = 'Sales' if sign == 1 else 'Refund'
        name = '%s untaxed' % title
        if applied_taxes:
            name = '%s with %s' % (title, ', '.join([tax.name for tax in applied_taxes]))
        base_tags = applied_taxes\
            .mapped('invoice_repartition_line_ids' if sign == 1 else 'refund_repartition_line_ids')\
            .filtered(lambda line: line.repartition_type == 'base')\
            .tag_ids
        partial_vals = {
            'name': name,
            'account_id': account_id,
            'move_id': self.move_id.id,
            'tax_ids': [(6, 0, tax_ids)],
            'tax_tag_ids': [(6, 0, base_tags.ids)],
        }
        return self._credit_amounts(partial_vals, amount, amount_converted)












