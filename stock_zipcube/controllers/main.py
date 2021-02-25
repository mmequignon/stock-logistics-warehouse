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
        cubiscan._update_packaging_measures(data)
        return True


TEST_STRING = """
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"barcode":"xyz", "weight": 12.3, '\
  '"length": 123, "width": 456, "height": 789}' \
  http://localhost:8069/stock/zipcube/1/measurement
"""
