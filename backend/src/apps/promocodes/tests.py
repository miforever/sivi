"""Promocodes tests."""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.promocodes.models import Promocode


class PromocodeTestCase(TestCase):
    """Tests for Promocode model."""

    def setUp(self):
        self.promocode = Promocode.objects.create(
            code="SAVE10", discount_percent=10, max_uses=100, is_active=True
        )

    def test_promocode_creation(self):
        self.assertEqual(self.promocode.code, "SAVE10")
        self.assertEqual(self.promocode.discount_percent, 10)
        self.assertTrue(self.promocode.is_valid)


class PromocodeAPITestCase(TestCase):
    """Tests for Promocode API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.promocode = Promocode.objects.create(
            code="SAVE10", discount_percent=10, max_uses=100, is_active=True
        )

    def test_validate_promocode(self):
        response = self.client.post("/api/v1/promocodes/validate/", {"code": "SAVE10"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["code"], "SAVE10")

    def test_validate_invalid_code(self):
        response = self.client.post("/api/v1/promocodes/validate/", {"code": "INVALID"})
        self.assertEqual(response.status_code, 404)

    def test_get_details(self):
        response = self.client.get("/api/v1/promocodes/details/?code=SAVE10")
        self.assertEqual(response.status_code, 200)
