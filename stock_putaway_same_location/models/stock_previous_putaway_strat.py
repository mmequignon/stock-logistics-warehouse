# Copyright (C) 2018 by Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models

class StockPreviousPutawayStrat(models.Model):
    _name = 'stock.previous.putaway.strat'
    _auto = False

    @api.model
    def get_closest_empty_sublocation(self, root_location=False):
        """Ordered by Z-Y-X successively in ascending order."""
        if not root_location:
            root_location = self.env.ref('stock.stock_location_stock')
        return self.env['stock.location'].search([
            '|',
            ('quant_ids.quantity', '=', 0.),
            ('quant_ids', '=', False),
            ('usage', '=', 'internal'),
            ('location_id', 'child_of', root_location.id),
        ], order='posz asc, posy asc, posx asc', limit=1)

    @api.model
    def get_most_recent_location(self, product, root_location=False):
        """Return most recent location that received that product.

        Most recent location is a `location_dest_id` of a most recent
        `stock.move.line` (ordered by date, then by ID) ending in a location
        under the given `root_location`.

        :param product: a product to search moves for
        :param root_location: defaults to WH/Stock
        """
        if not root_location:
            root_location = self.env.ref('stock.stock_location_stock')
        last_known_move = self.env['stock.move.line'].search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('location_dest_id', 'child_of', root_location.id),
        ], order='date desc, id desc', limit=1)
        return last_known_move.location_dest_id

    @api.model
    def putaway_apply(self, product):
        """Return the suggested destination location for given product."""
        # TODO handle multiple warehouses
        last_recent_location = self.get_most_recent_location(product)
        if last_recent_location:
            return last_recent_location
        return self.get_closest_empty_sublocation()
