# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class PosProductCostAccess(models.AbstractModel):
    _name = "pos.product.cost.access"
    _description = "Allow reading product cost during PoS load"

    @api.model
    def _has_field_access(self, field, operation):
        # Odoo 19 field ACLs go through _has_field_access / _check_field_access,
        # not the deprecated check_field_access_rights hook used in 18.0.
        if (
            operation == "read"
            and field.name == "standard_price"
            and self.env.context.get("pos_override_cost_security")
            and self.env.user.has_group("point_of_sale.group_pos_user")
            and not self.env.user.has_group("product_cost_security.group_product_cost")
        ):
            return True
        return super()._has_field_access(field, operation)

    def check_field_access_rights(self, operation, field_names):
        override_cost_security = (
            self.env.context.get("pos_override_cost_security")
            and self.env.user.has_group("point_of_sale.group_pos_user")
            and not self.env.user.has_group("product_cost_security.group_product_cost")
            and "standard_price" in (field_names or [])
        )
        if override_cost_security:
            return super(PosProductCostAccess, self.sudo()).check_field_access_rights(
                operation, field_names
            )
        return super().check_field_access_rights(operation, field_names)
