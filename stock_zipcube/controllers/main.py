# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, http
from odoo.exceptions import MissingError
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZipcubeController(http.Controller):
    @http.route("/stock/zipcube/<int:id_>/measurement", type="json", auth="none")
    def measurement(self, id_):
        env = request.env(su=True)
        cubiscan = env["cubiscan.device"].browse(id_)
        if not cubiscan:
            raise MissingError(_("No such cubiscan"))
        data = request.jsonrequest
        expected_keys = ["barcode", "weight", "length", "width", "height"]
        if set(data) != set(expected_keys):
            _logger.error("wrong data format: %s", data)
            raise ValueError("the data format is incorrect")
        _logger.info("received %s", data)
        # convert the float values passed as strings to floats
        for key in expected_keys[1:]:
            value = data[key]
            if isinstance(value, str):
                value = float(value.replace(",", "."))
                if key != "weight":
                    # lengths are in cm -> convert to mm
                    value *= 10
                data[key] = value
        cubiscan._update_packaging_measures(data)
        return True


TEST_STRING = """
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"barcode":"xyz", "weight": "12,3",'\
  '"length": "123,1", "width": "456,5", "height": "789,2"}' \
  https://integration.cosanum.odoo.camptocamp.ch/stock/zipcube/1/measurement
"""
