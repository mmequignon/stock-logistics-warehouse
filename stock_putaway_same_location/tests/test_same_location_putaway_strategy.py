# Copyright (C) 2018 by Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime
from odoo.tests import common


class SameLocationPutawayCase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Common data
        cls.location_stock = cls.env.ref('stock.stock_location_stock')
        tested_putaway_strategy = cls.env['product.putaway'].create({
            'name': 'Tested putaway strategy',
            'method': 'previous/empty',
        })
        cls.location_stock.putaway_strategy_id = tested_putaway_strategy
        cls.any_customer = cls.env['res.partner'].search([
            ('customer', '=', True),
        ])

        # Sublocations, a.k.a. "bins"
        cls.bins = cls.env['stock.location']

        # Prevent other sub-stock locations from being considered the closest
        cls.env['stock.location'].search([
            ('id', 'child_of', cls.location_stock.id),
            ('id', '!=', cls.location_stock.id),
        ]).write({
            'posx': 100,
            'posy': 100,
            'posz': 100,
        })

        for bin_number, coords in enumerate([
            (1, 1, 1),
            (2, 1, 1),
            (1, 2, 1),
            (2, 2, 1),
            (1, 3, 1),
            (2, 3, 1),
            (1, 1, 2),
        ], start=1):
            x, y, z = coords
            new_bin = cls.location_stock.create({
                'name': 'Bin #{} @ {}:{}:{}'.format(bin_number, x, y, z),
                'location_id': cls.location_stock.id,
                'usage': 'internal',
                'posx': x,
                'posy': y,
                'posz': z,
            })
            cls.bins |= new_bin

        # recompute `parent_left` and `parent_right`
        cls.env['stock.location']._parent_store_compute()

        # Products (differ in tracking)
        cls.product_a_untracked = cls.env['product.product'].create({
            'name': 'Sample product (untracked)',
            'tracking': 'none',
            'type': 'product',
        })
        cls.product_b_lots = cls.env['product.product'].create({
            'name': 'Sample product (tracked by lots)',
            'tracking': 'lot',
            'type': 'product',
        })
        cls.product_c_serial = cls.env['product.product'].create({
            'name': 'Sample product (tracked by SN-s)',
            'tracking': 'serial',
            'type': 'product',
        })

        # Purchase orders
        any_supplier = cls.env['res.partner'].search([
            ('supplier', '=', True),
        ], limit=1)
        cls.purchase_orders = cls.env['purchase.order']
        # PO00001
        cls.purchase_orders += cls.env['purchase.order'].create({
            'partner_id': any_supplier.id,
            'order_line': [
                (0, 0, cls._get_order_line_common_vals(
                    cls.product_a_untracked, 10)),
            ],
        })
        # PO00002
        cls.purchase_orders += cls.env['purchase.order'].create({
            'partner_id': any_supplier.id,
            'order_line': [
                (0, 0, cls._get_order_line_common_vals(
                    cls.product_a_untracked, 10)),
                (0, 0, cls._get_order_line_common_vals(
                    cls.product_b_lots, 20)),
            ],
        })
        # PO00003
        cls.purchase_orders += cls.env['purchase.order'].create({
            'partner_id': any_supplier.id,
            'order_line': [
                (0, 0, cls._get_order_line_common_vals(
                    cls.product_c_serial, 1)),
                (0, 0, cls._get_order_line_common_vals(
                    cls.product_b_lots, 15)),
            ],
        })
        # PO00004
        cls.purchase_orders += cls.env['purchase.order'].create({
            'partner_id': any_supplier.id,
            'order_line': [
                (0, 0, cls._get_order_line_common_vals(
                    cls.product_b_lots, 10)),
                (0, 0, cls._get_order_line_common_vals(
                    cls.product_c_serial, 1)),
            ],
        })
        # PO00005
        cls.purchase_orders += cls.env['purchase.order'].create({
            'partner_id': any_supplier.id,
            'order_line': [
                (0, 0, cls._get_order_line_common_vals(
                    cls.product_b_lots, 20)),
            ],
        })

    @staticmethod
    def _get_order_line_common_vals(product, qty2order):
        """Assemble vals for `purchase.order.line` creation."""
        return {
            'product_id': product.id,
            'product_qty': float(qty2order),
            # trash required by model's `create()`
            'name': '{} {} of {}'.format(
                qty2order, product.uom_id.name, product.name),
            'date_planned': datetime.today(),
            'product_uom': product.uom_id.id,
            'price_unit': 1337.,
        }

    def _create_manual_picking(
            self, product, location_from, location_to, qty, lot_name=False):
        intermediate_move = self.env['stock.move'].create({
            'name': 'whatever',
            'location_id': location_from.id,
            'location_dest_id': location_to.id,
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': qty,
            'move_line_ids': [
                (0, 0, {
                    'location_id': location_from.id,
                    'location_dest_id': location_to.id,
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'qty_done': qty,
                    'lot_id': self.env['stock.production.lot'].search([
                        ('name', '=', lot_name),
                    ]).id,
                }),
            ],
        })
        intermediate_move._assign_picking()
        self._process_pickings(intermediate_move.picking_id)
        return intermediate_move.picking_id

    def _validate_purchaseorder_picking(self, po, product_to_lot_names=None):
        """Validate a given purchase order, then confirm it's transfer."""
        po.button_approve()
        # provide lots for pickings
        self._process_pickings(po.picking_ids, product_to_lot_names)

    def _process_pickings(self, pickings, product_to_lot_names=None):
        if product_to_lot_names:
            for product, lot_name in product_to_lot_names:
                product_move_line = pickings.move_line_ids.filtered(
                    lambda m: m.product_id == product)
                lot = self.env['stock.production.lot'].search([
                    ('name', '=', lot_name),
                ])
                if lot:
                    product_move_line.lot_id = lot
                else:
                    product_move_line.lot_name = lot_name
        self.env['stock.immediate.transfer'].create({
            'pick_ids': [(6, 0, pickings.ids)],
        }).process()

    def _assert_amount_in_bin(self, product, bin_, xpected_qty):
        self.assertAlmostEqual(product.with_context(
            location=bin_.id,
            compute_child=False,
        ).qty_available, float(xpected_qty))

    def _assert_empty(self, location):
        self.assertAlmostEqual(sum(location.mapped('quant_ids.quantity')), 0.)

    def test_picking_validation(self):
        sample_po = self.purchase_orders[0]
        self._validate_purchaseorder_picking(sample_po)
        self.assertEqual(sample_po.picking_ids.mapped('state'), ['done'])
        self.assertGreater(self.product_a_untracked.with_context(
            location=self.location_stock.id,
        ).qty_available, 0.)

    def test_putaway_scenario_last_or_empty(self):

        # STEP 1: confirm PO00001
        # untracked (x10) => bins[0] // as an unknown product (first empty)
        po1 = self.purchase_orders[0]
        self._assert_empty(self.bins[0])
        self._validate_purchaseorder_picking(po1)
        self._assert_amount_in_bin(self.product_a_untracked, self.bins[0], 10)

        # STEP 2: confirm PO00002
        # untracked (x10) => bins[0] // as a most recent destination location
        # by lots   (x20) => bins[1] // as an unknown product (first empty)
        po2 = self.purchase_orders[1]
        self._assert_empty(self.bins[1])
        self._validate_purchaseorder_picking(po2, product_to_lot_names=[
            (self.product_b_lots, '001'),
        ])
        self._assert_amount_in_bin(self.product_a_untracked, self.bins[0], 20)
        self._assert_amount_in_bin(self.product_b_lots, self.bins[1], 20)

        # Step 2.5: manually move 10x of lot 001 // bins[1] => bins[3]
        # NOTE: bins[1] won't become empty after confirmation
        # cause that one holds 20 pcs of it ATM
        self._create_manual_picking(
            self.product_b_lots, self.bins[1], self.bins[3], 10., '001')
        self._assert_amount_in_bin(self.product_b_lots, self.bins[3], 10)

        # STEP 3: confirm PO00003
        # by lots   (x15) => bins[3] // as a most recent destination location
        # by SN-s   ( x1) => bins[2] // as an unknown product (first empty)
        po3 = self.purchase_orders[2]
        self._assert_empty(self.bins[2])
        self._validate_purchaseorder_picking(po3, product_to_lot_names=[
            (self.product_b_lots, '001'),
            (self.product_c_serial, '002'),
        ])
        # ensure that putaway strategy respects move that happened on step 2.5
        self._assert_amount_in_bin(self.product_b_lots, self.bins[3], 25)
        self._assert_amount_in_bin(self.product_c_serial, self.bins[2], 1)

        # STEP 4: confirm PO00004
        # by lots   (x10) => bins[3] // as a most recent destination location
        # by SN-s   ( x1) => bins[2] // as a most recent destination location
        po4 = self.purchase_orders[3]
        self._validate_purchaseorder_picking(po4, product_to_lot_names=[
            (self.product_b_lots, '003'),
            (self.product_c_serial, '005'),
        ])
        self._assert_amount_in_bin(self.product_b_lots, self.bins[3], 35)
        # ensure that bins[2] holds two products tracked by SN-s
        self._assert_amount_in_bin(self.product_c_serial, self.bins[2], 2)

        # Step 4.5: Create a delivery for 45 product B
        # NOTE: this dries out the whole product B stock
        self._create_manual_picking(
            self.product_b_lots,
            self.location_stock,
            self.env.ref('stock.stock_location_customers'),
            45.,
        )
        self._assert_empty(self.bins[1])
        self._assert_empty(self.bins[3])

        # STEP 5: confirm PO00005
        # by lots   (x20) => bins[3] // as a most recent destination location
        po5 = self.purchase_orders[4]
        self._validate_purchaseorder_picking(po5, product_to_lot_names=[
            (self.product_b_lots, '004'),
        ])
        self._assert_amount_in_bin(self.product_b_lots, self.bins[3], 20)
