"""Subscriptions tests."""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.subscriptions.models import Subscription, SubscriptionPlan
from apps.users.models import User


class SubscriptionPlanTestCase(TestCase):
    """Tests for SubscriptionPlan model."""

    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            plan_id="monthly",
            name="Monthly Plan",
            price=9.99,
            duration_days=30,
            features=["feature1", "feature2"],
        )

    def test_plan_creation(self):
        self.assertEqual(self.plan.plan_id, "monthly")
        self.assertEqual(str(self.plan), "Monthly Plan ($9.99)")


class SubscriptionTestCase(TestCase):
    """Tests for Subscription model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.plan = SubscriptionPlan.objects.create(
            plan_id="monthly",
            name="Monthly Plan",
            price=9.99,
            duration_days=30,
        )
        self.subscription = Subscription.objects.create(
            user=self.user, plan=self.plan, status="active"
        )

    def test_subscription_creation(self):
        self.assertEqual(self.subscription.user, self.user)
        self.assertEqual(self.subscription.plan, self.plan)
        self.assertEqual(self.subscription.status, "active")


class SubscriptionAPITestCase(TestCase):
    """Tests for Subscription API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.plan = SubscriptionPlan.objects.create(
            plan_id="monthly", name="Monthly Plan", price=9.99, duration_days=30, is_active=True
        )

    def test_get_plans(self):
        response = self.client.get("/api/v1/subscriptions/plans/list_plans/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get("data", [])), 1)

    def test_activate_subscription(self):
        response = self.client.post(
            "/api/v1/subscriptions/activate/",
            {"plan_id": "monthly", "user_id": str(self.user.id), "payment_id": "pay_123"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["status"], "active")

    def test_get_subscription_status(self):
        Subscription.objects.create(user=self.user, plan=self.plan, status="active")
        response = self.client.get(f"/api/v1/subscriptions/status/?user_id={self.user.id}")
        self.assertEqual(response.status_code, 200)
