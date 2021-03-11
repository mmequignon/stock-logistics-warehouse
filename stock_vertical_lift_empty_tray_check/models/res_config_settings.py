from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vertical_lift_empty_tray_check = fields.Boolean("Check Empty Tray", default=False)

    def set_values(self):
        super().set_values()
        icp = self.env["ir.config_parameter"]
        icp.set_param(
            "vertical_lift_empty_tray_check", self.vertical_lift_empty_tray_check
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        icp = self.env["ir.config_parameter"]
        vertical_lift_empty_tray_check = icp.get_param("vertical_lift_empty_tray_check")
        res.update({"vertical_lift_empty_tray_check": vertical_lift_empty_tray_check})
        return res
