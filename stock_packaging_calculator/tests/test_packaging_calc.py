# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import SavepointCase


class TestCalc(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product", "default_code": "A"}
        )
        cls.pkg_box = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_a.id, "qty": 50}
        )
        cls.pkg_big_box = cls.env["product.packaging"].create(
            {"name": "Big Box", "product_id": cls.product_a.id, "qty": 200}
        )
        cls.pkg_pallet = cls.env["product.packaging"].create(
            {"name": "Pallet", "product_id": cls.product_a.id, "qty": 2000}
        )
        cls.single_unit = cls.env.ref("uom.product_uom_unit")

    def test_calc_1(self):
        self.assertEqual(
            self.product_a.product_qty_by_packaging(2655),
            [(1, "Pallet"), (3, "Big Box"), (1, "Box"), (5, self.single_unit.name)],
        )

    def test_calc_2(self):
        self.assertEqual(
            self.product_a.product_qty_by_packaging(350), [(1, "Big Box"), (3, "Box")]
        )

    def test_calc_3(self):
        self.assertEqual(
            self.product_a.product_qty_by_packaging(80),
            [(1, "Box"), (30, self.single_unit.name)],
        )

    def test_calc_4(self):
        self.assertEqual(
            self.product_a.product_qty_by_packaging(80, min_unit=(5, "Pack 5")),
            [(1, "Box"), (6, "Pack 5")],
        )

    def test_calc_5(self):
        self.assertEqual(
            self.product_a.product_qty_by_packaging(80, min_unit=False), [(1, "Box")]
        )
