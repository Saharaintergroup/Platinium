from odoo import api, fields, models


class ProductKit(models.Model):
    _name = 'product.kit.component'
    _description = 'Product Kit Component'
    _check_company_auto = True

    product_id = fields.Many2one(
        comodel_name='product.template', string='Kit', required=True, ondelete='cascade')

    company_id = fields.Many2one(
        related='product_id.company_id', string='Company')

    product_component_id = fields.Many2one(
        comodel_name='product.product', string='Product', required=True, check_company=True)

    uom_id = fields.Many2one(related='product_id.uom_id', string='UOM')
    quantity = fields.Float('Quantity')

    currency_id = fields.Many2one(
        related='product_id.currency_id', string='Currency')

    component_currency_id = fields.Many2one(
        related='product_component_id.currency_id', string='Component Currency')

    price_unit = fields.Float('Unit Price', compute='_compute_price')
    price_subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_price')

    # should be context depending?
    @api.depends('quantity', 'product_component_id')
    def _compute_price(self):
        for kit_component in self:
            product_currency = kit_component.currency_id
            component_currency_id = kit_component.component_currency_id
            if component_currency_id.id and product_currency.id != component_currency_id.id:  # ask ghaith
                company = kit_component.company_id or self.env.company
                kit_price_component_currency = component_currency_id._convert(
                    kit_component.product_component_id.list_price, product_currency, company, fields.Datetime.today())
            else:
                kit_price_component_currency = kit_component.product_component_id.list_price

            kit_component.price_unit = kit_price_component_currency
            kit_component.price_subtotal = kit_price_component_currency * kit_component.quantity
