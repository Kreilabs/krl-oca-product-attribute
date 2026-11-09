# Copyright 2026 Tecnativa - Carlos Roca
# Copyright 2026 Kreilabs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import api, fields, models
from odoo.addons.stock_account.models.product import ProductProduct as StockAccountProductProduct


class ProductProduct(models.Model):
    _inherit = "product.product"

    avg_cost = fields.Monetary(
        groups="product_cost_security.group_product_cost",
        compute_sudo=True,
    )
    total_value = fields.Monetary(
        groups="product_cost_security.group_product_cost",
        compute_sudo=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Revalue a real cost without reading it in the caller's environment.

        ``stock_account`` reads ``standard_price`` while creating. Users who
        may create the product but cannot see its cost never reach that read:
        the stock_account override is skipped and, when the create payload
        actually sets a cost, revaluation runs on the elevated recordset.
        """
        products = super(StockAccountProductProduct, self).create(vals_list)
        if any(vals.get("standard_price") for vals in vals_list):
            valued = products._sudo_for_cost_valuation()
            valued._change_standard_price(
                {product: 0 for product in valued},
                valuation_date=datetime.min,
            )
        return products

    def _change_standard_price(self, old_price, valuation_date=None):
        """Revalue through the normal override chain, on an elevated recordset.

        ``sudo()`` would otherwise let the core lot search ignore company
        rules. The company ids live on the environment, not in the context,
        and only for this call.
        """
        records = self._sudo_for_cost_valuation()
        old_price = {
            product.with_env(records.env): price
            for product, price in old_price.items()
        }
        env = records.env
        previous = getattr(env, "_cost_valuation_company_ids", None)
        env._cost_valuation_company_ids = env.companies.ids
        try:
            return super(ProductProduct, records)._change_standard_price(
                old_price,
                valuation_date=valuation_date,
            )
        finally:
            if previous is None:
                delattr(env, "_cost_valuation_company_ids")
            else:
                env._cost_valuation_company_ids = previous

    def _update_standard_price(self, extra_value=None, extra_quantity=None):
        records = self._sudo_for_cost_valuation()
        return super(ProductProduct, records)._update_standard_price(
            extra_value=extra_value,
            extra_quantity=extra_quantity,
        )
