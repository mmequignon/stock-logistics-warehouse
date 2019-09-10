# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression
from odoo.tools.float_utils import float_compare


class StockReserveRule(models.Model):
    _name = "stock.reserve.rule"
    _description = "Stock Reservation Rule"
    _order = "sequence"

    name = fields.Char(string="Description")
    display_name = fields.Char(compute="_compute_display_name", store=True)
    sequence = fields.Integer(default=0)
    # required if no child
    location_id = fields.Many2one(
        comodel_name="stock.location",
        # TODO allow zone + stock
        domain=[("kind", "=", "zone")],
    )
    # TODO for now there is no support at all of parent,
    # what we could do is only leaves of the tree must have
    # a location, when a leaf is evaluated, we evaluate the
    # parents first
    parent_id = fields.Many2one(
        comodel_name="stock.reserve.rule", ondelete="cascade"
    )
    child_ids = fields.One2many(
        comodel_name="stock.reserve.rule", inverse_name="parent_id"
    )
    rule_domain = fields.Char(string="Domain", default=[])
    # TODO ACL + default value
    company_id = fields.Many2one(comodel_name="res.company")
    active = fields.Boolean(default=True)
    # TODO move in additional module
    only_full_quantity = fields.Boolean(default=False)
    # TODO tags stored on procurement.group?

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if any(not rule._check_recursion() for rule in self):
            raise exceptions.ValidationError(_("Rules cannot be recursive."))

    @api.depends("name", "location_id")
    def _compute_display_name(self):
        for rule in self:
            display_name = rule.name if rule.name else ""
            if rule.location_id:
                display_name = "%s (%s)" % (
                    display_name,
                    rule.location_id.display_name,
                )
            rule.display_name = display_name

    # TODO cache?
    def _rules_for_location(self, location):
        domain = [("location_id", "child_of", location.id)]
        return self.search(domain)

    def _rule_eval(self, move, need, quants_by_location):
        """Evaluate if the rule can be applied on move

        Return a boolean. True means the location can be used
        to reserve goods for the move.

        You can add new rules by inheriting this method.

        :param move: the move to reserve
        :param need: still needed quantity
        :param quants_by_location: dict with location as key and candidate quants
        as values
        :return: list of tuples(location, quantity) where goods can be reserved
        """
        # TODO add evaluation of parent rules before children
        # TODO if we want to support parent conditions, we'll have
        # to cache result of the parent and/or build a graph to
        # prevent double execution
        base_locations = self.env["stock.location"].browse(
            l.id for l in quants_by_location
        )

        locations = self.env["stock.location"].browse(base_locations.ids)

        domain = safe_eval(self.rule_domain) or []
        if domain:
            domain_locs = self._rule_eval_domain(
                move, quants_by_location, domain
            )
            locations -= base_locations - domain_locs

        if self.only_full_quantity:
            full_locs = self._rule_eval_only_full_quantity(
                move, need, quants_by_location
            )
            locations -= base_locations - full_locs

        result = []
        for location in locations:
            quants = quants_by_location[location]
            # TODO helper to get quantity properly
            location_quantity = sum(quants.mapped("quantity")) - sum(
                quants.mapped("reserved_quantity")
            )
            result.append((location, location_quantity))
        return result

    def _rule_eval_domain(self, move, quants_by_location, domain):
        move_domain = [("id", "=", move.id)]
        # TODO if we build a domain with dotted path such
        # as group_id.is_urgent (hypothetic field), can become very
        # slow if odoo searchs all "procurement.group.is_urgent" first
        # then uses "IN group_ids" on the stock move only.
        # Maybe a dynamic domain is a wishful thinking and we should only
        # have some pre-defined python methods.
        if self.env["stock.move"].search(
            expression.AND([move_domain, domain])
        ):
            return self.env["stock.location"].browse(
                l.id for l in quants_by_location
            )
        return self.env["stock.location"].browse()

    # TODO lot, ...?
    def _rule_eval_only_full_quantity(self, move, need, quants_by_location):
        rounding = move.product_id.uom_id.rounding
        # the goal of this rule is to empty locations, we pick products
        # only if we take everything from it, so "need" >= available
        locations = self.env["stock.location"].browse()
        for location, quants in quants_by_location.items():
            # TODO helper to get quantity properly
            # (see Quant._get_available_quantity)
            location_quantity = sum(quants.mapped("quantity")) - sum(
                quants.mapped("reserved_quantity")
            )
            # we'll empty a bin so we add this location to the list
            if float_compare(need, location_quantity, rounding) != -1:
                locations |= location
        return locations
