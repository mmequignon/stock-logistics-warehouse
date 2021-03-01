# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CubiscanWizard(models.TransientModel):
    _inherit = "cubiscan.wizard"

    def reload(self):
        return {
            "type": "ir.actions.act_view_reload",
        }

    device_driver = fields.Selection(related="device_id.driver")


class CubiscanWizardLine(models.TransientModel):
    _inherit = "cubiscan.wizard.line"

    scan_requested = fields.Boolean()

    def cubiscan_measure(self):
        self.ensure_one()
        res = super().cubiscan_measure()
        if self.wizard_id.device_id.driver == "zipcube":
            self.scan_requested = True
            self.packaging_id.scan_device_id = self.wizard_id.device_id
        return res
