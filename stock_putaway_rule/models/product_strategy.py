# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPutawayRule(models.Model):
    _name = 'stock.putaway.rule'
    _order = 'sequence,product_id'
    _description = 'Putaway Rule'

    def _default_category_id(self):
        if self.env.context.get('active_model') == 'product.category':
            return self.env.context.get('active_id')

    def _default_location_id(self):
        if self.env.context.get('active_model') == 'stock.location':
            return self.env.context.get('active_id')

    def _default_product_id(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'product.template' and active_id:
            product_template = self.env['product.template'].browse(active_id)
            product_template = product_template.exists()
            if product_template.product_variant_count == 1:
                return product_template.product_variant_id
        elif active_model == 'product.product':
            return active_id

    def _domain_category_id(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if (
            active_model in ('product.template', 'product.product')
            and active_id
        ):
            product = self.env[active_model].browse(active_id)
            product = product.exists()
            if product:
                return [('id', '=', product.categ_id.id)]
        return []

    def _domain_product_id(self):
        domain = "[('type', '!=', 'service'), " \
                 "'|', " \
                 "('company_id', '=', False), " \
                 "('company_id', '=', company_id)]"
        if self.env.context.get('active_model') == 'product.template':
            return [
                ('product_tmpl_id', '=', self.env.context.get('active_id'))
            ]
        return domain

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        default=lambda s: s._default_product_id(),
        domain=_domain_product_id,
        ondelete='cascade'
    )
    category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        default=lambda s: s._default_category_id(),
        domain=_domain_category_id,
        ondelete='cascade'
    )
    location_in_id = fields.Many2one(
        'stock.location',
        string='When product arrives in',
        domain="[('child_ids', '!=', False), "
               "'|', "
               "('company_id', '=', False), "
               "('company_id', '=', company_id)]",
        default=lambda s: s._default_location_id(),
        required=True,
        ondelete='cascade'
    )
    location_out_id = fields.Many2one(
        'stock.location',
        string='Store to',
        domain="[('id', 'child_of', location_in_id), "
               "('id', '!=', location_in_id), "
               "'|', "
               "('company_id', '=', False), "
               "('company_id', '=', company_id)]",
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(
        'Priority',
        help="Give to the more specialized category, a higher priority to "
             "have them in top of the list."
    )
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda s: s.env.user.company_id, index=True)

    @api.onchange('location_in_id')
    def _onchange_location_in(self):
        if self.location_out_id:
            child_location_count = self.env['stock.location'].search_count([
                ('id', '=', self.location_out_id.id),
                ('id', 'child_of', self.location_in_id.id),
                ('id', '!=', self.location_in_id.id),
            ])
            if not child_location_count:
                self.location_out_id = None

    def write(self, vals):
        if 'company_id' in vals:
            for rule in self:
                if rule.company_id.id != vals['company_id']:
                    raise UserError(_(
                        "Changing the company of this record is forbidden at "
                        "this point, you should rather archive it and create "
                        "a new one."
                    ))
        return super(StockPutawayRule, self).write(vals)
