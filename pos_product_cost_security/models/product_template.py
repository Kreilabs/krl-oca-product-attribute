# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "pos.product.cost.access"]

    @api.model
    def _load_pos_data_search_read(self, data, config):
        # Template search_read is the main catalog loader in Odoo 19 and also
        # reads standard_price; set the override before that path runs.
        self = self.with_context(pos_override_cost_security=True)
        return super()._load_pos_data_search_read(data, config)
