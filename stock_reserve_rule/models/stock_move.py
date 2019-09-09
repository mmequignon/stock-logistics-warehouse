# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models
from odoo.tools.float_utils import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    def _update_reserved_quantity(
        self,
        need,
        available_quantity,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=True,
    ):
        """Create or update move lines."""
        if strict:
            # chained moves must take what was reserved by the previous move
            return super()._update_reserved_quantity(
                need,
                available_quantity,
                location_id=location_id,
                lot_id=lot_id,
                package_id=package_id,
                owner_id=owner_id,
                strict=strict,
            )
        rules = self.env["stock.reserve.rule"]._rules_for_location(location_id)
        # TODO normal behavior if no rules found?
        still_need = need
        forced_package_id = self.package_level_id.package_id or None
        # get_available = self.env["stock.quant"]._get_available_quantity
        rounding = self.product_id.uom_id.rounding
        for rule in rules:
            # TODO lot, ... (see Quant._get_available_quantity)
            quants_by_loc = self.env["stock.quant"]._gather_by_location(
                self.product_id,
                rule.location_id,
                lot_id=lot_id,
                package_id=forced_package_id,
                owner_id=owner_id,
                strict=strict,
            )
            match_locations = rule._rule_eval(self, still_need, quants_by_loc)

            if not match_locations:
                continue
            for location, location_quantity in match_locations:
                if location_quantity <= 0:
                    continue

                taken_in_loc = super()._update_reserved_quantity(
                    still_need,
                    location_quantity,
                    location_id=location,
                    lot_id=lot_id,
                    package_id=package_id,
                    owner_id=owner_id,
                    strict=strict,
                )
                still_need -= taken_in_loc
                need_zero = (
                    float_compare(still_need, 0, precision_rounding=rounding)
                    != 1
                )
                if need_zero:
                    # useless to eval the other rules when still_need <= 0
                    break

        # TODO call super with the rest and a location?
        return need - still_need
