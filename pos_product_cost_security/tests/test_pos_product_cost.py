# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from odoo.addons.point_of_sale.tests.common import CommonPosTest


@tagged("post_install", "-at_install")
class TestPosProductCostSecurity(CommonPosTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.ten_dollars_no_tax.product_variant_id
        cls.product.standard_price = 10.0
        cls.pos_cashier = new_test_user(
            cls.env,
            "pos_cashier_no_cost",
            groups="base.group_user,point_of_sale.group_pos_user",
        )

    def _read_product(self, user, context_values, fields=None):
        if fields is None:
            fields = ["name", "standard_price"]
        # Use env(user=) so pos.load.mixin.with_user does not inject the override.
        env = self.env(user=user, context=dict(self.env.context, **context_values))
        return env["product.product"].browse(self.product.id).read(fields)

    def test_read_with_override_context(self):
        self.assertFalse(
            self.pos_cashier.has_group("product_cost_security.group_product_cost")
        )
        product_data = self._read_product(
            self.pos_cashier, {"pos_override_cost_security": True}
        )
        self.assertIn("name", product_data[0])
        self.assertIn(
            "standard_price",
            product_data[0],
            "Standard price should be visible with override",
        )
        self.assertEqual(
            product_data[0]["standard_price"],
            self.product.sudo().standard_price,
            "Standard price should match the product cost",
        )

    def test_read_without_override_raises(self):
        with self.assertRaises(AccessError):
            self._read_product(self.pos_cashier, {})

    def test_pos_load_data_without_cost_group(self):
        self.assertFalse(
            self.pos_cashier.has_group("product_cost_security.group_product_cost")
        )
        self.pos_config_usd.open_ui()
        session = self.pos_config_usd.current_session_id
        # Simulate the POS frontend: the request already runs as the cashier,
        # without going through with_user() on pos.load.mixin.
        cashier_session = self.env(user=self.pos_cashier)["pos.session"].browse(
            session.id
        )
        data = cashier_session.load_data([])
        templates = data["product.template"]
        products = data["product.product"]
        self.assertTrue(
            templates, "PoS must load product templates for a cashier without cost access"
        )
        self.assertTrue(
            products, "PoS must load products for a cashier without cost access"
        )
        loaded = next(item for item in products if item["id"] == self.product.id)
        self.assertIn("standard_price", loaded)
        self.assertEqual(loaded["standard_price"], self.product.sudo().standard_price)
