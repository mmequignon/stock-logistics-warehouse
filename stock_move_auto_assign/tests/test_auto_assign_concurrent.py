# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from contextlib import contextmanager

from odoo import api
from odoo.modules.registry import Registry
from odoo.tests import common, tagged
from odoo.tools import mute_logger

from odoo.addons.queue_job.exception import RetryableJobError

from .common import StockMoveAutoAssignCase


@tagged("post_install", "-at_install")
class TestStockMoveAutoAssignConcurrent(StockMoveAutoAssignCase):
    @classmethod
    @contextmanager
    def simulate_other_request(cls):
        current_environment = api.Environment._local.environments
        try:
            api.Environment._local.environments = api.Environments()
            yield
        finally:
            api.Environment._local.environments = current_environment

    def test_job_assign_diff_transaction_assign_moves(self):
        """Different transactions assign 2 moves of the same picking"""
        # we need the picking to exist before, otherwise the other transaction
        # would not be aware of it
        picking = self.env.ref("stock_move_auto_assign.outgoing_shipment_auto_assign")
        move1 = picking.move_lines[0]
        # browse the move2 in the second env, from now on, will take care of
        # move1 in the first env and move2 in the second
        product1 = move1.product_id

        self._update_qty_in_location(self.shelf1_loc, product1, 1000)

        product1.moves_auto_assign(self.shelf1_loc)
        self.assertEqual(move1.state, "assigned")

        # As the envs are shared in api.Environments in the same request, it's
        # not enough to only open a new env. Open a detached api.Environments too.
        with self.simulate_other_request():
            registry2 = Registry(common.get_db_name())
            cr2 = registry2.cursor()
            env2 = api.Environment(cr2, self.env.uid, {})

            @self.addCleanup
            def reset_cr2():
                # rollback and close the cursor, and reset the environments
                env2.reset()
                cr2.rollback()
                cr2.close()

            move2 = picking.move_lines[1].with_env(env2)
            product2 = move2.product_id
            self._update_qty_in_location(self.shelf1_loc.with_env(env2), product2, 1000)

            with mute_logger("openerp.sql_db"), self.assertRaises(RetryableJobError):
                product2.moves_auto_assign(self.shelf1_loc.with_env(env2))
        # the picking would not be confirmed here if 2 requests (or jobs)
        # called moves_auto_assign for the 2 moves at the same time and we had
        # no lock
