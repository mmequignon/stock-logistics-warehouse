# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.osv import expression


class StockMove(models.Model):
    _inherit = "stock.move"

    virtual_reserved_qty = fields.Float(
        "Virtual Reserved Quantity",
        compute="_compute_virtual_reserved_qty",
        help="Quantity to be reserved by older operations that do not have"
        " a real reservation yet",
    )

    @api.depends()
    def _compute_virtual_reserved_qty(self):
        for move in self:
            if (
                move.location_id.should_bypass_reservation()
                or move.product_id.type == "consu"
                or move.procure_method == "make_to_order"
                or move.move_orig_ids
            ):
                move.virtual_reserved_qty = 0.
                continue
            forced_package_id = move.package_level_id.package_id or None
            available = self.env["stock.quant"]._get_available_quantity(
                move.product_id, move.location_id, package_id=forced_package_id
            )
            move.virtual_reserved_qty = max(
                min(
                    available - move._virtual_reserved_qty(), self.product_qty
                ),
                0.,
            )

    def _virtual_quantity_domain(self, location_id=None):
        states = ("draft", "confirmed", "partially_available", "waiting")
        domain = [
            ("state", "in", states),
            ("product_id", "=", self.product_id.id),
            # TODO easier way to customize date field to use
            ("procure_method", "=", "make_to_stock"),
            # ("location_dest_id.usage", "=", "customer"),
            ("date", "<=", self.date),
            # TODO do we need to check sublocations?
            (
                "location_id",
                "child_of",
                location_id.id if location_id else self.location_id.id,
            ),
        ]
        # TODO priority?
        return domain

    def _virtual_reserved_qty(self, location_id=None):
        previous_moves = self.search(
            expression.AND(
                [
                    self._virtual_quantity_domain(location_id=location_id),
                    [("id", "!=", self.id)],
                ]
            )
        )
        virtual_reserved = sum(
            previous_moves.mapped(
                lambda move: max(
                    move.product_qty - move.reserved_availability, 0.
                )
            )
        )
        return virtual_reserved

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
        # TODO how to ensure this is done before any other override of the
        # method...
        if not strict:
            virtual_reserved = self._virtual_reserved_qty(
                location_id=location_id
            )
            available_quantity = max(available_quantity - virtual_reserved, 0.)
        return super()._update_reserved_quantity(
            need,
            available_quantity,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )
