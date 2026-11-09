# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import Form
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestProductCostSecurity(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Prevent errors when the stock module is installed
        # and attempting to change standard_price
        # Without this flag in the context,
        # the system tries to access stock.move, which the user may not have permission.
        cls.env = cls.env(context=dict(cls.env.context, disable_auto_svl=True))
        cls.base_group_user_id = cls.env.ref("base.group_user").id
        cls.product_edit_cost_group_id = cls.env.ref(
            "product_cost_security.group_product_edit_cost"
        ).id
        cls.product_cost_group_id = cls.env.ref(
            "product_cost_security.group_product_cost"
        ).id
        cls.product_template_model = cls.env["product.template"]
        cls.env.user.write(
            {"group_ids": [Command.set(cls.env.ref("base.group_system").ids)]}
        )

    def _user_without_cost(self):
        return new_test_user(
            self.env,
            "no_cost_user",
            groups="base.group_user,product.group_product_manager",
        )

    def test_system_user_inherits_cost_groups(self):
        system_user = new_test_user(self.env, "sys_cost_user", groups="base.group_system")
        self.assertTrue(
            system_user.has_group("product_cost_security.group_product_cost")
        )
        self.assertTrue(
            system_user.has_group("product_cost_security.group_product_edit_cost")
        )

    def test_without_access_to_product_costs_group(self):
        sheet_form = Form(
            self.product_template_model.with_user(self._user_without_cost())
        )
        sheet_form.name = "Test Product"
        sheet_form.save()
        with self.assertRaises(AssertionError):
            # It would raise an AssertionError as the field would not be found
            # in the view as the user does not have the group- Access to
            # product costs
            standard_price = sheet_form.standard_price
            self.assertEqual(standard_price, 0.0)

    def test_with_access_to_product_costs_group(self):
        self.env.user.group_ids = [
            Command.set(
                [
                    self.product_cost_group_id,
                    self.base_group_user_id,
                    self.env.ref("product.group_product_manager").id,
                ]
            )
        ]
        sheet_form = Form(self.product_template_model.with_user(self.env.user))
        sheet_form.name = "Test Product"
        sheet_form.save()
        standard_price = (
            sheet_form.standard_price
        )  # It would not raise any error now as the user
        # has the required group to view the costs
        self.assertEqual(standard_price, 0.0)

    def test_without_access_to_modify_product_costs_group(self):
        sheet_form = Form(
            self.product_template_model.with_user(self._user_without_cost())
        )
        sheet_form.name = "Test Product"
        sheet_form.save()
        with self.assertRaises(AssertionError):
            # It would raise an AssertionError as the field is readonly in the view
            # as the user does not have the group- Modify product costs
            sheet_form.standard_price = 5.0

    def test_with_access_to_modify_product_costs_group(self):
        self.env.user.group_ids = [
            Command.set(
                [
                    self.product_edit_cost_group_id,
                    self.base_group_user_id,
                    self.env.ref("product.group_product_manager").id,
                ]
            )
        ]
        sheet_form = Form(self.product_template_model.with_user(self.env.user))
        sheet_form.name = "Test Product"
        sheet_form.save()
        sheet_form.standard_price = 5.0  # It would not raise any error now as the user
        # has the required group to modify the costs
        self.assertEqual(sheet_form.standard_price, 5.0)

    def test_api_modification(self):
        """Test that a direct API call respects the security groups."""
        # Using base.group_system because it's the only group in this module's
        # dependency graph with CRUD access to products
        editor = new_test_user(
            self.env,
            "editor",
            groups="product.group_product_manager,product_cost_security.group_product_edit_cost",
        )
        reader = new_test_user(
            self.env,
            "reader",
            groups="product.group_product_manager,product_cost_security.group_product_cost",
        )
        user = new_test_user(
            self.env, "user", groups="base.group_user,product.group_product_manager"
        )
        # Editor can write and read
        product = (
            self.env["product.product"]
            .with_user(editor)
            .create(
                {
                    "name": "Test product",
                    "standard_price": 10.0,
                }
            )
        )
        self.assertEqual(
            product.read(["standard_price"]),
            [{"id": product.id, "standard_price": 10.0}],
        )
        product.standard_price = 20.0
        self.assertEqual(
            product.read(["standard_price"]),
            [{"id": product.id, "standard_price": 20.0}],
        )
        # Reader can read but not write
        product = product.with_user(reader)
        with self.assertRaises(AccessError):
            product.standard_price = 30.0
        self.assertEqual(
            product.read(["standard_price"]),
            [{"id": product.id, "standard_price": 20.0}],
        )
        # User can't read or write (standard Odoo when setting field groups)
        product = product.with_user(user)
        with self.assertRaises(AccessError):
            product.standard_price = 30.0
        with self.assertRaises(AccessError):
            product.read(["standard_price"])
        # Sudo still works
        product.sudo().standard_price = 30.0
        self.assertEqual(
            product.sudo().read(["standard_price"]),
            [{"id": product.id, "standard_price": 30.0}],
        )

    def test_valuation_context_does_not_grant_cost_read(self):
        """RPC context must not reveal costs on read, search, export or groups."""
        editor = new_test_user(
            self.env,
            "context_editor",
            groups="product.group_product_manager,product_cost_security.group_product_edit_cost",
        )
        product = (
            self.env["product.product"]
            .with_user(editor)
            .create({"name": "Context cost", "standard_price": 12.0})
        )
        user = new_test_user(
            self.env,
            "context_no_cost",
            groups="product.group_product_manager,base.group_allow_export",
        )
        product_user = product.with_user(user).with_context(
            _product_cost_security_valuation=True
        )
        template_user = product.product_tmpl_id.with_user(user).with_context(
            _product_cost_security_valuation=True
        )
        for record in (product_user, template_user):
            with self.assertRaises(AccessError):
                record.read(["standard_price"])
            with self.assertRaises(AccessError):
                record.search_read([("id", "=", record.id)], ["standard_price"])
            with self.assertRaises(AccessError):
                record.export_data(["name", "standard_price"])
            with self.assertRaises(AccessError):
                record.read_group(
                    [("id", "=", record.id)],
                    [],
                    ["standard_price:sum"],
                )
        visible = product_user.search_read([("id", "=", product.id)], ["name"])
        self.assertEqual(visible[0]["name"], "Context cost")
        self.assertNotIn("standard_price", visible[0])
        self.assertEqual(product.sudo().standard_price, 12.0)

    def test_export_without_cost_permission(self):
        """UC-03: export must not expose cost to unauthorized users."""
        editor = new_test_user(
            self.env,
            "export_editor",
            groups="base.group_system,product_cost_security.group_product_edit_cost",
        )
        product = (
            self.env["product.product"]
            .with_user(editor)
            .create({"name": "Export test product", "standard_price": 42.0})
        )
        exporter = new_test_user(
            self.env,
            "export_user",
            groups="base.group_user,stock.group_stock_user,base.group_allow_export",
        )
        with self.assertRaises(AccessError):
            product.with_user(exporter).read(["standard_price"])
        export_name = product.with_user(exporter).export_data(["name"])
        self.assertEqual(export_name["datas"][0][0], "Export test product")
        with self.assertRaises(AccessError):
            product.with_user(exporter).export_data(["name", "standard_price"])

    def test_read_without_edit_and_read_group(self):
        """A user who can see the cost cannot change it, including via grouping."""
        editor = new_test_user(
            self.env,
            "group_editor",
            groups="product.group_product_manager,product_cost_security.group_product_edit_cost",
        )
        reader = new_test_user(
            self.env,
            "group_reader",
            groups=(
                "product.group_product_manager,"
                "product_cost_security.group_product_cost,"
                "base.group_allow_export"
            ),
        )
        product = (
            self.env["product.product"]
            .with_user(editor)
            .create({"name": "Grouped cost", "standard_price": 8.0})
        )
        grouped = product.with_user(reader).read_group([], [], ["standard_price:avg"])
        self.assertTrue(grouped)
        found = product.with_user(reader).search_read(
            [("id", "=", product.id)],
            ["standard_price"],
        )
        self.assertEqual(found[0]["standard_price"], 8.0)
        exported = product.with_user(reader).export_data(["standard_price"])
        self.assertEqual(exported["datas"][0][0], 8.0)
        with self.assertRaises(AccessError):
            product.with_user(reader).write({"standard_price": 9.0})
        with self.assertRaises(AccessError):
            product.with_user(reader).with_context(
                _product_cost_security_valuation=True
            ).write({"standard_price": 9.0})
        self.assertEqual(product.sudo().standard_price, 8.0)
        outsider = new_test_user(
            self.env,
            "group_outsider",
            groups="base.group_user",
        )
        with self.assertRaises(AccessError):
            self.env["product.product"].with_user(outsider).read_group(
                [("id", "=", product.id)],
                [],
                ["standard_price:sum"],
            )

    def test_company_isolation(self):
        company_b = self.env["res.company"].sudo().create({"name": "Cost company B"})
        product_b = (
            self.env["product.product"]
            .sudo()
            .with_company(company_b)
            .create(
                {
                    "name": "Product company B",
                    "company_id": company_b.id,
                    "standard_price": 77.0,
                }
            )
        )
        user_a = new_test_user(
            self.env,
            "company_a_cost_user",
            groups="product.group_product_manager,product_cost_security.group_product_edit_cost",
            company_id=self.env.company.id,
            company_ids=[Command.set(self.env.company.ids)],
        )
        self.assertFalse(
            self.env["product.product"]
            .with_user(user_a)
            .search([("id", "=", product_b.id)])
        )
        with self.assertRaises(AccessError):
            product_b.with_user(user_a).write({"standard_price": 1.0})
        with self.assertRaises(AccessError):
            product_b.with_user(user_a).with_context(
                _product_cost_security_valuation=True
            ).read(["standard_price"])
