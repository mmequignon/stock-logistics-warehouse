# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from itertools import groupby

from odoo import api, models
from odoo.tools.float_utils import float_compare

import logging

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _gather_by_location(
        self,
        product_id,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
    ):
        quants = self.env["stock.quant"]._gather(
            product_id,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )
        # TODO take care of product's tracking type...
        by_location = {}
        for quant in quants:
            by_location.setdefault(quant.location_id, self.browse())
            by_location[quant.location_id] |= quant

        return by_location
