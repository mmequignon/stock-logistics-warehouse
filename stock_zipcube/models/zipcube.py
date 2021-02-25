# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CubiscanDevice(models.Model):
    _inherit = "cubiscan.device"

    driver = fields.Selection(selection_add=[("zipcube", "Zipcube")])

    def _update_packaging_measures(self, measures):
        self.ensure_one()
        packaging = self.env["product.packaging"].search(
            [("scan_device_id", "=", self.id)], order="write_date DESC"
        )
        if len(packaging) == 0:
            _logger.error("Could not find packaging to update by device %s", self)
            raise UserError(_("No package found pending a scan by this device"))
        elif len(packaging) > 1:
            _logger.warning(
                "Several packagings (%s) found to update by device %s", packaging, self
            )
            _logger.warning("Will update the 1st %s", packaging[0])
        to_update = packaging[0]
        wizard_line = self.env["cubiscan.wizard.line"].search(
            [
                ("packaging_id", "=", to_update.id),
                ("wizard_id.device_id", "=", self.id),
            ],
            order="write_date DESC",
            limit=1,
        )
        if not wizard_line:
            _logger.warning("no wizard line found for this measure")
        wizard_line.write(
            {
                "lngth": measures["length"],
                "width": measures["width"],
                "height": measures["height"],
                "max_weight": measures["max_weight"],
            }
        )
        packaging.write({"scan_device_id": False})
        return to_update
