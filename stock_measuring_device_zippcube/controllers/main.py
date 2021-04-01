# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging
import os

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZippcubeController(http.Controller):
    DEVICE_SECRET_KEY = "ZIPPCUBE_SECRET"

    weight_keys = ("weight",)
    measures_keys = ("length", "width", "height")
    expected_keys = ("secret", "barcode") + weight_keys + measures_keys

    @http.route(
        "/stock/zippcube/<string:zippcube_device_name>/measurement",
        type="json",
        auth="none",
    )
    def measurement(self, zippcube_device_name):
        data = request.jsonrequest
        _logger.info("/measurement, data received: {}".format(data))

        env = request.env(su=True)
        zippcube = env["zippcube.device"].search(
            [("name", "=", zippcube_device_name)], limit=1
        )
        if not zippcube:
            raise MissingError(
                _("No such Zippcube with name {}.".format(zippcube_device_name))
            )

        keys_missing = set(self.expected_keys) - set(data)
        if keys_missing:
            error_msg = _(
                "Wrong data format: {}. Keys missing: {}.".format(data, keys_missing)
            )
            _logger.error(error_msg)
            raise ValueError(error_msg)

        self._check_secret(data["secret"])
        # convert the float values passed as strings to floats
        data = self._convert_floats(data)
        zippcube._update_packaging_measures(data)
        return True

    def _convert_floats(self, data):
        for key in self.weight_keys + self.measures_keys:
            value = data[key]
            if isinstance(value, str):
                value = float(value.replace(",", "."))
                if key in self.measures_keys:
                    # lengths are in cm -> convert to mm
                    value *= 10
                data[key] = value
        return data

    def _device_get_secret(self):
        return os.environ.get(self.DEVICE_SECRET_KEY)

    def _check_secret(self, secret):
        if secret and secret == self._device_get_secret():
            return True
        else:
            raise AccessError()
