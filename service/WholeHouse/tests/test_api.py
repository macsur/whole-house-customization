# 一期 REST API 冒烟测试：统一信封、需求提交、管理端鉴权。
from django.contrib.auth.models import User
from django.test import TestCase

from api.models import Customer, Product, Requirement


class EnvelopeApiTests(TestCase):
    def test_health_returns_unified_envelope(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.json(), {
            "code": 200, "message": "success",
            "data": {"status": "ok", "service": "whole-house-api"},
        })

    def test_products_list_envelope(self):
        Product.objects.create(name="测试系列", category="厨房", style="现代欧式")
        response = self.client.get("/api/products")
        payload = response.json()
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["message"], "success")
        self.assertEqual(payload["data"]["total"], 1)
        self.assertEqual(payload["data"]["items"][0]["name"], "测试系列")

    def test_submit_requirement_creates_customer_and_requirement(self):
        response = self.client.post("/api/customize", {
            "contact": "测试客人", "phone": "13900009999", "space": "厨房",
            "style": "现代欧式", "budget": "8–12 万元",
        }, format="json")
        self.assertEqual(response.json()["code"], 200)
        self.assertEqual(Requirement.objects.count(), 1)
        self.assertTrue(Customer.objects.filter(phone="13900009999").exists())

    def test_submit_requirement_rejects_invalid_phone(self):
        response = self.client.post("/api/customize", {
            "contact": "测试客人", "phone": "123", "space": "厨房",
        }, format="json")
        self.assertEqual(response.json()["code"], 400)
        self.assertEqual(Requirement.objects.count(), 0)

    def test_admin_entities_requires_staff_token(self):
        from rest_framework.authtoken.models import Token

        response = self.client.get("/api/entities?entity=requirements")
        self.assertEqual(response.status_code, 401)

        staff = User.objects.create_superuser("admin_test", "a@example.com", "x12345678")
        token = Token.objects.create(user=staff)
        response = self.client.get(
            "/api/entities?entity=requirements",
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        self.assertEqual(response.json()["code"], 200)

    def test_client_user_cannot_admin_login(self):
        User.objects.create_user("13800000001", password="x12345678")
        response = self.client.post("/api/admin/login", {
            "account": "13800000001", "password": "x12345678",
        }, format="json")
        self.assertEqual(response.json()["code"], 403)

    def test_client_register_hashes_password(self):
        response = self.client.post("/api/register", {
            "name": "新用户", "phone": "13800000002", "password": "x12345678",
        }, format="json")
        self.assertEqual(response.json()["code"], 200)
        user = User.objects.get(username="13800000002")
        self.assertNotIn("x12345678", user.password)
        self.assertTrue(user.check_password("x12345678"))
