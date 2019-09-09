# Copyright 2019 Camptocamp (https://www.camptocamp.com)

from odoo.tests import common


class TestReserveRule(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_delta = cls.env.ref("base.res_partner_4")
        cls.wh = cls.env["stock.warehouse"].create(
            {
                "name": "Base Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "pick_ship",
                "code": "WHTEST",
            }
        )

        cls.customer_loc = cls.env.ref("stock.stock_location_customers")

        cls.loc_zone1 = cls.env["stock.location"].create(
            {
                "name": "Zone1",
                "location_id": cls.wh.lot_stock_id.id,
                "kind": "zone",
            }
        )
        cls.loc_zone1_bin1 = cls.env["stock.location"].create(
            {
                "name": "Zone1 Bin1",
                "location_id": cls.loc_zone1.id,
                "kind": "bin",
            }
        )
        cls.loc_zone1_bin2 = cls.env["stock.location"].create(
            {
                "name": "Zone1 Bin2",
                "location_id": cls.loc_zone1.id,
                "kind": "bin",
            }
        )
        cls.loc_zone2 = cls.env["stock.location"].create(
            {
                "name": "Zone2",
                "location_id": cls.wh.lot_stock_id.id,
                "kind": "zone",
            }
        )
        cls.loc_zone2_bin1 = cls.env["stock.location"].create(
            {
                "name": "Zone2 Bin1",
                "location_id": cls.loc_zone2.id,
                "kind": "bin",
            }
        )
        cls.loc_zone2_bin2 = cls.env["stock.location"].create(
            {
                "name": "Zone2 Bin2",
                "location_id": cls.loc_zone2.id,
                "kind": "bin",
            }
        )
        cls.loc_zone3 = cls.env["stock.location"].create(
            {
                "name": "Zone3",
                "location_id": cls.wh.lot_stock_id.id,
                "kind": "zone",
            }
        )
        cls.loc_zone3_bin1 = cls.env["stock.location"].create(
            {
                "name": "Zone3 Bin1",
                "location_id": cls.loc_zone3.id,
                "kind": "bin",
            }
        )
        cls.loc_zone3_bin2 = cls.env["stock.location"].create(
            {
                "name": "Zone3 Bin2",
                "location_id": cls.loc_zone3.id,
                "kind": "bin",
            }
        )

        cls.product1 = cls.env["product.product"].create(
            {"name": "Product 1", "type": "product"}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Product 2", "type": "product"}
        )

    def _create_picking(self, wh, products=None):
        """Create picking

        Products must be a list of tuples (product, quantity).
        One stock move will be created for each tuple.
        """
        if products is None:
            products = []

        picking = self.env["stock.picking"].create(
            {
                "location_id": wh.lot_stock_id.id,
                "location_dest_id": wh.wh_output_stock_loc_id.id,
                "partner_id": self.partner_delta.id,
                "picking_type_id": wh.pick_type_id.id,
            }
        )

        for product, qty in products:
            self.env["stock.move"].create(
                {
                    "name": product.name,
                    "product_id": product.id,
                    "product_uom_qty": qty,
                    "product_uom": product.uom_id.id,
                    "picking_id": picking.id,
                    "location_id": wh.lot_stock_id.id,
                    "location_dest_id": wh.wh_output_stock_loc_id.id,
                    "state": "confirmed",
                }
            )
        return picking

    def _update_qty_in_location(self, location, product, quantity):
        self.env["stock.quant"]._update_available_quantity(
            product, location, quantity
        )

    def _create_rules(self, rule_values):
        for values in rule_values:
            self.env["stock.reserve.rule"].create(values)

    def test_rule_take_all_in_2(self):
        all_locs = (
            self.loc_zone1_bin1,
            self.loc_zone1_bin2,
            self.loc_zone2_bin1,
            self.loc_zone2_bin2,
            self.loc_zone3_bin1,
            self.loc_zone3_bin2,
        )
        for loc in all_locs:
            self._update_qty_in_location(loc, self.product1, 100)

        picking = self._create_picking(self.wh, [(self.product1, 200)])

        self._create_rules(
            [
                {"location_id": self.loc_zone1.id, "sequence": 2},
                {"location_id": self.loc_zone2.id, "sequence": 1},
                {"location_id": self.loc_zone3.id, "sequence": 3},
            ]
        )

        picking.action_assign()
        move = picking.move_lines
        ml = move.move_line_ids
        self.assertRecordValues(
            ml,
            [
                {"location_id": self.loc_zone2_bin1.id, "product_qty": 100},
                {"location_id": self.loc_zone2_bin2.id, "product_qty": 100},
            ],
        )
        self.assertEqual(move.state, "assigned")

    def test_rule_take_all_in_2_and_3(self):
        self._update_qty_in_location(self.loc_zone1_bin1, self.product1, 100)
        self._update_qty_in_location(self.loc_zone2_bin1, self.product1, 100)
        self._update_qty_in_location(self.loc_zone3_bin1, self.product1, 100)
        picking = self._create_picking(self.wh, [(self.product1, 150)])

        self._create_rules(
            [
                {"location_id": self.loc_zone1.id, "sequence": 3},
                {"location_id": self.loc_zone2.id, "sequence": 1},
                {"location_id": self.loc_zone3.id, "sequence": 2},
            ]
        )

        picking.action_assign()
        move = picking.move_lines
        ml = move.move_line_ids
        self.assertRecordValues(
            ml,
            [
                {"location_id": self.loc_zone2_bin1.id, "product_qty": 100},
                {"location_id": self.loc_zone3_bin1.id, "product_qty": 50},
            ],
        )
        self.assertEqual(move.state, "assigned")

    def test_rule_remaining(self):
        self._update_qty_in_location(self.loc_zone1_bin1, self.product1, 100)
        self._update_qty_in_location(self.loc_zone2_bin1, self.product1, 100)
        self._update_qty_in_location(self.loc_zone3_bin1, self.product1, 100)
        picking = self._create_picking(self.wh, [(self.product1, 400)])

        self._create_rules(
            [
                {"location_id": self.loc_zone1.id, "sequence": 3},
                {"location_id": self.loc_zone2.id, "sequence": 1},
                {"location_id": self.loc_zone3.id, "sequence": 2},
            ]
        )

        picking.action_assign()
        move = picking.move_lines
        ml = move.move_line_ids
        self.assertRecordValues(
            ml,
            [
                {"location_id": self.loc_zone2_bin1.id, "product_qty": 100},
                {"location_id": self.loc_zone3_bin1.id, "product_qty": 100},
                {"location_id": self.loc_zone1_bin1.id, "product_qty": 100},
            ],
        )
        self.assertEqual(move.state, "partially_available")
        self.assertEqual(move.reserved_availability, 300.)

    def test_rule_domain(self):
        self._update_qty_in_location(self.loc_zone1_bin1, self.product1, 100)
        self._update_qty_in_location(self.loc_zone2_bin1, self.product1, 100)
        self._update_qty_in_location(self.loc_zone3_bin1, self.product1, 100)
        picking = self._create_picking(self.wh, [(self.product1, 200)])

        domain = [("product_id", "!=", self.product1.id)]
        self._create_rules(
            [
                # this rule should be excluded by the domain
                {
                    "location_id": self.loc_zone1.id,
                    "sequence": 1,
                    "rule_domain": domain,
                },
                {"location_id": self.loc_zone2.id, "sequence": 2},
                {"location_id": self.loc_zone3.id, "sequence": 3},
            ]
        )
        picking.action_assign()
        move = picking.move_lines
        ml = move.move_line_ids
        self.assertRecordValues(
            ml,
            [
                {"location_id": self.loc_zone2_bin1.id, "product_qty": 100},
                {"location_id": self.loc_zone3_bin1.id, "product_qty": 100},
            ],
        )
        self.assertEqual(move.state, "assigned")

    def test_rule_only_full_quantity(self):
        self._update_qty_in_location(self.loc_zone1_bin1, self.product1, 300)
        self._update_qty_in_location(self.loc_zone1_bin2, self.product1, 150)
        self._update_qty_in_location(self.loc_zone2_bin1, self.product1, 50)
        self._update_qty_in_location(self.loc_zone3_bin1, self.product1, 100)
        picking = self._create_picking(self.wh, [(self.product1, 250)])

        self._create_rules(
            [
                # This rule should be excluded for zone1 / bin1 because the
                # bin would not be empty, but applied on zone1 / bin2.
                {
                    "location_id": self.loc_zone1.id,
                    "sequence": 1,
                    "only_full_quantity": True,
                },
                # this rule should be applied because we will empty the bin
                {
                    "location_id": self.loc_zone2.id,
                    "sequence": 2,
                    "only_full_quantity": True,
                },
                {"location_id": self.loc_zone3.id, "sequence": 3},
            ]
        )
        picking.action_assign()
        move = picking.move_lines
        ml = move.move_line_ids

        self.assertRecordValues(
            ml,
            [
                {"location_id": self.loc_zone1_bin2.id, "product_qty": 150.},
                {"location_id": self.loc_zone2_bin1.id, "product_qty": 50.},
                {"location_id": self.loc_zone3_bin1.id, "product_qty": 50.},
            ],
        )
        self.assertEqual(move.state, "assigned")
