# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class MeasuringDevice(models.Model):
    _name = "measuring.device"
    _inherit = "collection.base"
    _description = "Measuring and Weighing Device"
    _order = "warehouse_id, name"

    name = fields.Char("Name", required=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse", required=True)
    device_type = fields.Selection(
        selection=[],
        help="The type of device (e.g. zippcube, cubiscan...) "
        "depending on which module are installed.",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique (name)",
            "The name of the measuring/weighing device must be unique.",
        ),
    ]

    def _forward(self, method, *args, **kwargs):
        _logger.debug(
            "Measuring Device ID: %s type %s > %s : %s %s",
            self.id,
            self.device_type,
            method,
            args,
            kwargs,
        )
        self.ensure_one()
        measuring_device = self._get_measuring_device()
        return getattr(measuring_device, method)(*args, **kwargs)

    def _get_measuring_device(self):
        with self.work_on(self._name) as work:
            return work.component(usage=self.device_type)

    def open_wizard(self):
        return {
            "name": _("Measurement Wizard"),
            "res_model": "measuring.wizard",
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "form",
            "context": {"default_device_id": self.id},
            "target": "fullscreen",
            "flags": {
                "withControlPanel": False,
                "form_view_initial_mode": "edit",
                "no_breadcrumbs": True,
            },
        }

    def _is_being_used(self):
        with self.work_on(self._name) as work:
            device = work.component(usage=self.device_type)
            return device._is_being_used()
