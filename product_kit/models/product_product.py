from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Product(models.Model):
    _inherit = 'product.product'

    def get_kit_price(self) -> float:
        self.ensure_one()
        kit_component_ids = self.product_component_ids
        if not kit_component_ids:
            return 0
        price = 0
        for kit_component in kit_component_ids:
            price += kit_component.price_subtotal
        return price

    @api.depends('is_kit', 'product_component_ids')
    def _compute_kit_price(self):
        for product in self:
            if not product.is_kit or product.pricing_kit_type == 'global':
                product.kit_price = 0
                continue
            product.kit_price = product.list_price = product.get_kit_price()

    @api.constrains('product_component_ids', 'is_kit')
    def _constrains_kit(self):
        for product in self:
            if product.is_kit and not product.product_component_ids:
                raise UserError(_('Please add components for the kit'))

    @api.onchange('is_kit', 'product_component_ids')
    def _onchange_kit(self):
        self.update({'list_price': self.get_kit_price()})
