# Copyright 2026 Kreilabs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    value = fields.Monetary(
        groups="product_cost_security.group_product_cost",
        compute_sudo=True,
    )
