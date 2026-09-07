# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "pos.product.cost.access"]

    @api.model
    def _load_pos_data_search_read(self, data, config):
        self = self.with_context(pos_override_cost_security=True)
        return super()._load_pos_data_search_read(data, config)
