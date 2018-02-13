# Copyright 2018 Camptocamp SA
# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

UNIT = dp.get_precision('Product Unit of Measure')


class ProductTemplate(models.Model):
    _inherit = "product.template"

    qty_available_not_res = fields.Float(
        string='Quantity On Hand Unreserved',
        digits=UNIT,
        compute='_compute_product_available_not_res',
    )

    qty_available_stock_text = fields.Char(
        compute='_compute_product_available_not_res',
        string='Unreserved stock quantity',
    )

    @api.multi
    @api.depends('product_variant_ids.qty_available_not_res')
    def _compute_product_available_not_res(self):
        no_new = self.filtered(lambda x: not isinstance(x.id, models.NewId))
        for tmpl in no_new:
            tmpl.qty_available_not_res = sum(
                tmpl.mapped('product_variant_ids.qty_available_not_res')
            )
            tmpl.qty_available_stock_text = "/".join(
                tmpl.mapped('product_variant_ids.qty_available_stock_text')
            )

    @api.multi
    def action_open_quants_unreserved(self):
        products = self.mapped('product_variant_ids').ids
        quants = self.env['stock.quant'].search(
            [
                ('product_id', 'in', products),
            ]
        )
        quant_ids = quants.filtered(
            lambda x: x.product_id.qty_available_not_res > 0
        ).ids
        result = self.env.ref('stock.product_open_quants').read()[0]
        result['domain'] = "[('id', 'in', {})]".format(quant_ids)
        result['context'] = "{'search_default_locationgroup': 1, " \
                            "'search_default_internal_loc': 1}"
        return result


class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_available_not_res = fields.Float(
        string='Qty Available Not Reserved',
        digits=UNIT,
        compute='_compute_qty_available_not_reserved',
    )

    qty_available_stock_text = fields.Char(
        compute='_compute_qty_available_not_reserved',
        string='Available per stock',
    )

    @api.multi
    def _product_available_not_res_hook(self, quants):
        """Hook used to introduce possible variations"""
        return False

    @api.multi
    def _prepare_domain_available_not_reserved(self):
        domain_quant = [
            ('product_id', 'in', self.ids),
            ('contains_unreserved', '=', True),
        ]
        domain_quant_locations = self._get_domain_locations()[0]
        domain_quant.extend(domain_quant_locations)
        return domain_quant

    @api.multi
    def _compute_product_available_not_res_dict(self):

        res = {}

        domain_quant = self._prepare_domain_available_not_reserved()
        quants = self.env['stock.quant'].with_context(lang=False).search(
            domain_quant,
        )
        for prod in self:
            vals = {}
            prod_quant = quants.filtered(lambda x: x.product_id == prod)
            quantity = sum(prod_quant.mapped(
                lambda x: x._get_available_quantity(
                    x.product_id,
                    x.location_id
                )
            ))
            vals['qty_available_not_res'] = quantity
            vals['qty_available_stock_text'] = str(quantity) + _(" On Hand")
            res[prod.id] = vals

        return res

    @api.multi
    def _compute_qty_available_not_reserved(self):
        res = self._compute_product_available_not_res_dict()
        for prod in self:
            qty = res[prod.id]['qty_available_not_res']
            text = res[prod.id]['qty_available_stock_text']
            prod.qty_available_not_res = qty
            prod.qty_available_stock_text = text
        return res
