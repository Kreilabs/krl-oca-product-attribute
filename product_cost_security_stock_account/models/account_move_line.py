# Copyright 2026 Kreilabs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.product_cost_security.models.product_cost_security_mixin import (
    sudo_for_cost_valuation,
)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_cogs_value(self):
        """COGS reads the product cost. Elevate that read without unlocking it."""
        self.ensure_one()
        if self.env.su or not self.product_id:
            return super()._get_cogs_value()
        product = sudo_for_cost_valuation(self.product_id, access="read")
        return super(AccountMoveLine, self.with_env(product.env))._get_cogs_value()
