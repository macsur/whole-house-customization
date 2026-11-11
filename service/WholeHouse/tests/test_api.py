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


class FloorPlanUploadTests(TestCase):
    """E1：户型图 multipart 上传。"""

    def test_multipart_upload_with_png_attachment(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile("户型.png", b"fake png", content_type="image/png")
        response = self.client.post("/api/requirements", {
            "contact": "附件测试", "phone": "13877778888", "space": "厨房",
            "budget": "5–8 万元", "floorPlan": upload,
        }, format="multipart")
        self.assertEqual(response.json()["code"], 200)
        data = response.json()["data"]
        self.assertEqual(data["has_attachment"], True)
        self.assertEqual(data["floor_plan_type"], "image/png")
        requirement = Requirement.objects.get(pk=data["id"])
        self.assertTrue(requirement.floor_plan_path)
        self.assertEqual(requirement.floor_plan_size, len(b"fake png"))
        # 文件确实落盘
        import os
        from django.conf import settings
        from api.attachments import media_root
        self.assertTrue(os.path.isfile(os.path.join(media_root(), requirement.floor_plan_path)))

    def test_upload_rejects_oversize(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile("big.pdf", b"x" * (10 * 1024 * 1024 + 1), content_type="application/pdf")
        response = self.client.post("/api/requirements", {
            "contact": "超限", "phone": "13877770000", "space": "厨房", "floorPlan": upload,
        }, format="multipart")
        self.assertEqual(response.json()["code"], 400)
        self.assertIn("10MB", response.json()["message"])
        self.assertEqual(Requirement.objects.count(), 0)

    def test_upload_rejects_wrong_type(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile("bad.txt", b"hello", content_type="text/plain")
        response = self.client.post("/api/requirements", {
            "contact": "类型", "phone": "13877771111", "space": "厨房", "floorPlan": upload,
        }, format="multipart")
        self.assertEqual(response.json()["code"], 400)
        self.assertIn("jpg/png/webp", response.json()["message"])

    def test_admin_download_requires_staff(self):
        response = self.client.get("/api/floorplan?requirement=1")
        self.assertEqual(response.status_code, 401)

    def test_admin_download_attachment(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from rest_framework.authtoken.models import Token

        upload = SimpleUploadedFile("户型.png", b"fake png content", content_type="image/png")
        created = self.client.post("/api/requirements", {
            "contact": "下载测试", "phone": "13877772222", "space": "厨房", "floorPlan": upload,
        }, format="multipart").json()["data"]["id"]

        staff = User.objects.create_superuser("dl_admin", "d@example.com", "x12345678")
        token = Token.objects.create(user=staff)
        response = self.client.get(
            f"/api/floorplan?requirement={created}",
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"fake png content")
