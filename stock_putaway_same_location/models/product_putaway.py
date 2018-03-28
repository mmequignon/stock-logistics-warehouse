# Copyright (C) 2018 by Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class ProductPutaway(models.Model):
    _inherit = 'product.putaway'

    @api.model
    def _get_putaway_options(self):
        res = super(ProductPutaway, self)._get_putaway_options()
        res.append(
            ('previous/empty', 'Previous location or empty one'),
        )
        return res

    # @override
    # super()::putaway_apply defined w/out @api.multi
    def putaway_apply(self, product):
        if self.method == 'previous/empty':
            return self.env['stock.previous.putaway.strat'] \
                .putaway_apply(product)
        return super().putaway_apply(product)
