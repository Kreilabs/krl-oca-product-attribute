# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class PosLoadMixin(models.AbstractModel):
    _inherit = "pos.load.mixin"

    @api.model
    def with_user(self, user):
        ctx = dict(self.env.context)
        ctx["pos_override_cost_security"] = True
        return super().with_user(user).with_context(**ctx)

    def with_env(self, env):
        ctx = dict(env.context)
        ctx["pos_override_cost_security"] = True
        return super().with_env(env(context=ctx))

    @api.model
    def _load_pos_data_read(self, records, config):
        # Odoo 19 load_data calls _load_pos_data_search_read without with_user,
        # so the mixin hooks never run. Force the override on the actual read.
        self = self.with_context(pos_override_cost_security=True)
        records = records.with_context(pos_override_cost_security=True)
        return super()._load_pos_data_read(records, config)
