# Copyright 2026 Tecnativa - Carlos Roca
# Copyright 2026 Kreilabs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.addons.product_cost_security.models.product_cost_security_mixin import (
    sudo_for_cost_valuation,
)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        """Value the move as superuser only when this user may write it.

        Completing the move reads product and lot costs. That read stays on
        the elevated recordset; the caller keeps its own environment, so the
        cost fields are not unlocked for later RPC reads.
        """
        records = sudo_for_cost_valuation(self, access="write")
        result = super(StockMove, records)._action_done(
            cancel_backorder=cancel_backorder
        )
        if isinstance(result, models.BaseModel):
            return result.with_env(self.env)
        return result
