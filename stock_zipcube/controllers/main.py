# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZipcubeController(http.Controller):
    weight_keys = ("weight",)
    measures_keys = ("length", "width", "height")
    expected_keys = ("secret", "barcode") + weight_keys + measures_keys

    @http.route("/stock/zipcube/<int:id_>/measurement", type="json", auth="none")
    def measurement(self, id_):
        env = request.env(su=True)
        cubiscan = env["cubiscan.device"].browse(id_)
        if not cubiscan:
            raise MissingError(_("No such cubiscan"))
        data = request.jsonrequest
        if set(data) != set(self.expected_keys):
            _logger.error("wrong data format: %s", data)
            raise ValueError("the data format is incorrect")
        _logger.info("received %s", data)
        self._check_secret(data["secret"])
        data = self._convert_floats(data)
        # convert the float values passed as strings to floats
        cubiscan._update_packaging_measures(data)
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

    def _check_secret(self, secret):
        if secret:
            # XXX
            return True
        else:
            raise AccessError()


TEST_STRING = """
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"secret": "abcdefg", "barcode":"xyz", "weight": "12,3",'\
  '"length": "123,1", "width": "456,5", "height": "789,2"}' \
  https://integration.cosanum.odoo.camptocamp.ch/stock/zipcube/1/measurement
"""
