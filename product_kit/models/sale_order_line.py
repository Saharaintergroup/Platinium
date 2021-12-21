from odoo import api, fields, models


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'
    # TODO add the function here

    origin_order_line = fields.Char('Originator Kit Line')
    kit_ref = fields.Char('Kit Line Refrence')


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.onchange('order_line')
    def _onchange_order_line_kit(self):
        """add lines for the components of the product.
        """

        added_sale_order_lines = self.order_line if not self.origin else self.order_line - \
            self.origin.order_line
        for sale_line in added_sale_order_lines:
            if not sale_line.product_id.is_kit:
                return

            kit_components = sale_line.product_id.product_component_ids

            if not kit_components:
                return

            else:
                new_kit_lines = []
                old_kit_lines = self.order_line.filtered(
                    lambda line: line.origin_order_line in [sale_line.id.ref, sale_line.kit_ref] or line.origin_order_line == sale_line.id.origin or line.origin_order_line == str(
                        sale_line.id.origin)
                )

                factor = sale_line.product_uom_qty

                if sale_line.product_uom.id and sale_line.product_uom.id != sale_line.product_id.uom_id.id:
                    factor = sale_line.product_id.uom_id._compute_quantity(
                        sale_line.product_uom, round=True, rounding_method='UP', raise_if_failure=True)
                for component in kit_components:
                    if component.product_component_id.id in old_kit_lines.mapped('product_id').ids:
                        old_line = old_kit_lines.filtered(
                            lambda line: line.product_id.id == component.product_component_id.id)
                        old_line.update(
                            {'product_uom_qty': component.quantity * factor})
                        continue
                    # set the price based on the pricing type of the kit
                    price_unit = 0 if sale_line.product_id.pricing_kit_type == 'global' else component.price_unit
                    # if the product currency price is not equal to the currency of the SO. we must do the conversion
                    if component.product_id.currency_id != self.currency_id and price_unit:
                        price_unit = component.product_id.currency_id._convert(price_unit, self.currency_id,
                                                                               self.company_id, fields.date.today(), round=True)
                    # if the uom of the product is not the one used in SO line we must do the conversion in order to get the price_unit
                    if component.product_id.uom_id != sale_line.product_uom and price_unit:
                        price_unit = component.product_id.uom_id._compute_price(
                            self, price_unit, sale_line.product_uom)
                    new_kit_lines.append((0, 0,
                                          {
                                              'product_id': component.product_component_id.id,
                                              'product_uom_qty': component.quantity * factor,
                                              'price_unit': price_unit,
                                              'origin_order_line': sale_line.id.ref or str(sale_line.id.origin),
                                              'product_uom': component.product_component_id.uom_id.id,
                                              'name': component.product_component_id.display_name

                                          }))
                    if sale_line.id.ref:
                        sale_line.update({
                            'kit_ref': sale_line.id.ref
                        })
                # create_kit_line_ids = self.create(new_kit_lines)
                # for new_line in create_kit_line_ids:
                # self.update({'kit_line_ids': [(4, new_line.id)]})
                self.update(
                    {'order_line': new_kit_lines})
