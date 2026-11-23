# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.fields import Domain


class StockLot(models.Model):
    _name = "stock.lot"
    _inherit = ["stock.lot", "product.cost.security.mixin"]

    standard_price = fields.Float(groups="product_cost_security.group_product_cost")
    avg_cost = fields.Monetary(groups="product_cost_security.group_product_cost")
    total_value = fields.Monetary(groups="product_cost_security.group_product_cost")

    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        company_ids = getattr(self.env, "_cost_valuation_company_ids", None)
        if company_ids is not None:
            domain = Domain(domain) & Domain(
                [("company_id", "in", list(company_ids) + [False])]
            )
        return super()._read_group(
            domain, groupby, aggregates, having, offset, limit, order
        )
