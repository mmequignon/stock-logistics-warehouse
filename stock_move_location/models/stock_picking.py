# Copyright Jacques-Etienne Baudoux 2016 Camptocamp
# Copyright Iryna Vyshnevska 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, models
from odoo.exceptions import UserError
from itertools import groupby


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_fillwithstock(self):
        # check source location has no children, i.e. we scanned a bin

        self.ensure_one()
        if self.location_id.child_ids:
            raise UserError(_('Please choose a source end location'))
        if self.move_lines:
            raise UserError(_('Moves lines already exists'))
        quants = self.env['stock.quant'].search(
            [
                ('location_id', 'child_of', self.location_id.id),
                ('quantity', '>', 0.0),
            ]
        )
        context = {
            'active_ids': quants.ids,
            'active_model': 'stock.quant',
        }
        move_wizard = self.env['wiz.stock.move.location'].with_context(context).create({
            'destination_location_id' : self.location_dest_id.id,
            'origin_location_id': self.location_id.id,
            'picking_type_id': self.picking_type_id.id,
            'picking_id': self.id,
        })
        move_wizard._onchange_destination_location_id()
        move_wizard.action_move_location()

        return True
