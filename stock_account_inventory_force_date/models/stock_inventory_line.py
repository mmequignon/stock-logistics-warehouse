# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    @api.depends('location_id', 'product_id', 'package_id',
                 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id',
                 'inventory_id.force_inventory_date')
    def _compute_theoretical_qty(self):
        forced = self.filtered(
            lambda line: line.inventory_id.force_inventory_date)
        self = self - forced
        res = super()._compute_theoretical_qty()
        for line in forced:
            if not line.product_id:
                line.theoretical_qty = 0
                continue
            if line.product_id.tracking == "none":
                product_at_date = self.env['product.product'].with_context({
                    'to_date': line.inventory_id.date,
                    'location': line.location_id.id,
                    'compute_child': False,
                }).browse(line.product_id.id)
                theoretical_qty = product_at_date.qty_available
                if theoretical_qty and line.product_uom_id and \
                        line.product_id.uom_id != line.product_uom_id:
                    theoretical_qty = line.product_id.uom_id._compute_quantity(
                        theoretical_qty, line.product_uom_id)
                line.theoretical_qty = theoretical_qty
            elif not line.prod_lot_id:
                # Keep theoretical_qty to 0 if no lot is defined
                line.theoretical_qty = 0
            else:
                res = self.env["stock.move.line"].get_lot_qty_at_date_in_location(
                    line.product_id,
                    line.location_id,
                    line.inventory_id.date,
                    lot=line.prod_lot_id
                )
                if res:
                    # TODO handle UOMs?
                    line.theoretical_qty = res[0].get("qty", 0)
                else:
                    line.theoretical_qty = 0
