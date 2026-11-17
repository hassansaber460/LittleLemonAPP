from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Cart, Category, MenuItem, Order, OrderItem


class LittleLemonAPITests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer", password="Strong-pass-123")
        self.manager = User.objects.create_user(username="manager", password="Strong-pass-123")
        self.admin = User.objects.create_user(
            username="admin", password="Strong-pass-123", is_staff=True
        )
        self.crew = User.objects.create_user(username="crew", password="Strong-pass-123")
        self.other_crew = User.objects.create_user(username="other-crew", password="Strong-pass-123")
        Group.objects.get_or_create(name="Manager")[0].user_set.add(self.manager)
        Group.objects.get_or_create(name="Delivery Crew")[0].user_set.add(self.crew)
        Group.objects.get_or_create(name="Delivery Crew")[0].user_set.add(self.other_crew)
        self.category = Category.objects.create(title="Main", slug="main")
        self.menu_item = MenuItem.objects.create(
            title="Grilled fish", price=Decimal("12.50"), featured=False, category=self.category
        )

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_customer_can_register_and_password_is_hashed(self):
        response = self.client.post(
            reverse("create-new-user"),
            {"username": "new-customer", "email": "new@example.com", "password": "Another-Strong-123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        created = User.objects.get(username="new-customer")
        self.assertTrue(created.check_password("Another-Strong-123"))
        self.assertNotIn("password", response.data)
        self.assertTrue(Token.objects.filter(user=created).exists())

    def test_login_returns_existing_token_and_rejects_invalid_credentials(self):
        self.authenticate(self.customer)
        token = Token.objects.get(user=self.customer).key
        self.client.credentials()
        response = self.client.post(
            reverse("login"),
            {"username": "customer", "password": "Strong-pass-123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["token"], token)
        denied = self.client.post(
            reverse("login"),
            {"username": "customer", "password": "wrong"},
            format="json",
        )
        self.assertEqual(denied.status_code, 400)

    def test_menu_is_readable_to_authenticated_user(self):
        self.authenticate(self.customer)
        response = self.client.get(reverse("menu-item-list"))
        self.assertEqual(response.status_code, 200)

    def test_only_manager_can_create_update_or_delete_menu_items(self):
        self.authenticate(self.customer)
        denied = self.client.post(
            reverse("menu-item-list"),
            {"title": "Lemon cake", "price": "5.00", "featured": True, "category_write": self.category.pk},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)
        self.authenticate(self.crew)
        denied_update = self.client.patch(
            reverse("menu-item-detail", args=[self.menu_item.title]), {"featured": True}, format="json
        )
        self.assertEqual(denied_update.status_code, 403)
        self.authenticate(self.manager)
        created = self.client.post(
            reverse("menu-item-list"),
            {"title": "Lemon cake", "price": "5.00", "featured": True, "category_write": self.category.pk},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        updated = self.client.patch(
            reverse("menu-item-detail", args=[self.menu_item.title]), {"featured": True}, format="json"
        )
        self.assertEqual(updated.status_code, 200)
        self.menu_item.refresh_from_db()
        self.assertTrue(self.menu_item.featured)
        deleted = self.client.delete(reverse("menu-item-detail", args=[self.menu_item.title]))
        self.assertEqual(deleted.status_code, 204)

    def test_cart_uses_database_price_and_is_user_scoped(self):
        self.authenticate(self.customer)
        response = self.client.post(
            reverse("cart"), {"menu_item": self.menu_item.pk, "quantity": 2, "unit_price": "0.01"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        item = Cart.objects.get(user=self.customer, menu_item=self.menu_item)
        self.assertEqual(item.unit_price, Decimal("12.50"))
        self.assertEqual(item.price, Decimal("25.00"))
        self.assertNotIn("user", response.data)

    def test_customer_can_create_order_and_cart_is_cleared(self):
        Cart.objects.create(
            user=self.customer, menu_item=self.menu_item, quantity=2,
            unit_price=Decimal("12.50"), price=Decimal("25.00"),
        )
        self.authenticate(self.customer)
        response = self.client.post(reverse("orders"), {}, format="json")
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(user=self.customer)
        self.assertEqual(order.total, Decimal("25.00"))
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertFalse(Cart.objects.filter(user=self.customer).exists())

    def test_customer_cannot_view_another_customers_order(self):
        other = User.objects.create_user(username="other", password="Strong-pass-123")
        order = Order.objects.create(user=other, total=Decimal("10.00"))
        self.authenticate(self.customer)
        response = self.client.get(reverse("order-detail", args=[order.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delivery_crew_only_sees_assigned_orders_and_can_update_status_only(self):
        own = Order.objects.create(user=self.customer, delivery_crew=self.crew, total=Decimal("10.00"))
        Order.objects.create(user=self.customer, delivery_crew=self.other_crew, total=Decimal("8.00"))
        self.authenticate(self.crew)
        listing = self.client.get(reverse("orders"))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([row["id"] for row in listing.data["results"]], [own.pk])
        update = self.client.patch(
            reverse("order-detail", args=[own.pk]), {"status": True}, format="json"
        )
        self.assertEqual(update.status_code, 200)
        forbidden = self.client.patch(
            reverse("order-detail", args=[own.pk]), {"total": "1.00"}, format="json"
        )
        self.assertEqual(forbidden.status_code, 400)
        hidden = self.client.get(reverse("order-detail", args=[2]))
        self.assertEqual(hidden.status_code, 404)

    def test_manager_can_assign_only_delivery_crew_members(self):
        order = Order.objects.create(user=self.customer, total=Decimal("10.00"))
        self.authenticate(self.manager)
        response = self.client.patch(
            reverse("order-detail", args=[order.pk]), {"delivery_crew": self.crew.pk}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.delivery_crew, self.crew)
        invalid = self.client.patch(
            reverse("order-detail", args=[order.pk]), {"delivery_crew": self.customer.pk}, format="json"
        )
        self.assertEqual(invalid.status_code, 400)

    def test_group_management_denies_non_admins(self):
        self.authenticate(self.manager)
        denied = self.client.get(reverse("manager-users"))
        self.assertEqual(denied.status_code, 403)
        self.authenticate(self.customer)
        denied_crew = self.client.post(
            reverse("delivery-crew-users"), {"username": self.customer.username}, format="json"
        )
        self.assertEqual(denied_crew.status_code, 403)

    def test_admin_can_manage_manager_group(self):
        self.authenticate(self.admin)
        response = self.client.post(
            reverse("manager-users"), {"username": self.customer.username}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.customer.groups.filter(name="Manager").exists())
