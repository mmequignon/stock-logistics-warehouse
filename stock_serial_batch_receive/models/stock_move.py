# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    picking_type_create_lots = fields.Boolean(
        related='picking_id.picking_type_id.use_create_lots',
        readonly=True
    )
    first_code = fields.Char(
        string='First code',
        help="First serial number to be generated for this stock move",
    )
    last_code = fields.Char(
        string='Last code',
        help="Last serial number to be generated for this stock move",
    )

    def open_generate_serials_wizard(self):
        action = self.env.ref(
            'stock_serial_batch_receive.'
            'act_stock_move_line_serial_generator').read()[0]
        return action
