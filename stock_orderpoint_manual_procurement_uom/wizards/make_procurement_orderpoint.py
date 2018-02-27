# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class MakeProcurementOrderpoint(models.TransientModel):
    _inherit = 'make.procurement.orderpoint'

    @api.model
    def _prepare_item(self, orderpoint):
        vals = super(MakeProcurementOrderpoint, self)._prepare_item(orderpoint)
        if orderpoint.procure_uom_id:
            product_uom = orderpoint.procure_uom_id
            vals['uom_id'] = product_uom.id
        return vals

    @api.multi
    def make_procurement(self):
        self.ensure_one()
        errors = []
        for item in self.item_ids:
            if not item.qty:
                raise ValidationError(_("Quantity must be positive."))
            if not item.orderpoint_id:
                raise ValidationError(_("No reordering rule found!"))
            qty = item.qty
            values = item.orderpoint_id._prepare_procurement_values(qty)
            if item.orderpoint_id.procure_uom_id:
                qty = item.orderpoint_id.procure_uom_id._compute_quantity(
                    qty, item.orderpoint_id.product_uom)
            # Run procurement
            try:
                self.env['procurement.group'].run(
                    item.orderpoint_id.product_id,
                    qty,
                    item.orderpoint_id.product_uom,
                    item.orderpoint_id.location_id,
                    item.orderpoint_id.name,
                    item.orderpoint_id.name,
                    values
                )
            except UserError as error:
                    errors.append(error.name)
            if errors:
                raise UserError('\n'.join(errors))

        return {'type': 'ir.actions.act_window_close'}


class MakeProcurementOrderpointItem(models.TransientModel):
    _inherit = 'make.procurement.orderpoint.item'

    @api.multi
    @api.onchange('uom_id')
    def onchange_uom_id(self):
        for rec in self:
            uom = rec.orderpoint_id.procure_uom_id or \
                rec.orderpoint_id.product_uom
            rec.qty = uom._compute_quantity(
                rec.orderpoint_id.procure_recommended_qty,
                rec.uom_id)
