# Copyright 2019 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Serial Sequence',
        help="Algorithm to generate serial numbers",
        copy=False,
    )
