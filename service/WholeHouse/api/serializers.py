# 序列化器：数据库字段 → 前端展示字段（保持与原静态数据字段口径一致）
from rest_framework import serializers

from .models import Case, Customer, Order, Product, Requirement


class ProductSerializer(serializers.ModelSerializer):
    features = serializers.JSONField(required=False)
    # 兼容管理端原表格字段口径
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True, format="%Y-%m-%d")

    class Meta:
        model = Product
        fields = [
            "id", "name", "category", "style", "material", "image",
            "description", "features", "status", "updated_at", "updatedAt",
        ]


class CaseSerializer(serializers.ModelSerializer):
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True, format="%Y-%m-%d")

    class Meta:
        model = Case
        fields = [
            "id", "name", "space", "style", "area", "image",
            "summary", "status", "updated_at", "updatedAt",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    # 兼容管理端原表格字段口径：count=需求数、lastContact=最近联系
    requirement_count = serializers.IntegerField(source="requirements.count", read_only=True)
    last_contact = serializers.DateTimeField(source="updated_at", read_only=True, format="%Y-%m-%d")
    count = serializers.SerializerMethodField()
    lastContact = serializers.DateTimeField(source="updated_at", read_only=True, format="%Y-%m-%d")

    def get_count(self, obj):
        return obj.requirements.count()

    class Meta:
        model = Customer
        fields = [
            "id", "name", "phone", "city", "address", "preferred_style",
            "email", "requirement_count", "count", "last_contact",
            "lastContact", "status", "created_at",
        ]


class RequirementSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True, default="")
    # 兼容管理端原表格字段口径：customer=客户名、submittedAt=提交时间
    customer = serializers.SerializerMethodField()
    submittedAt = serializers.DateTimeField(source="created_at", read_only=True, format="%Y-%m-%d %H:%M")
    has_attachment = serializers.SerializerMethodField()

    def get_customer(self, obj):
        return obj.customer.name if obj.customer else ""

    class Meta:
        model = Requirement
        fields = [
            "id", "customer", "customer_name", "contact", "phone", "space",
            "house_type", "dimensions", "style", "materials", "budget",
            "delivery_date", "description", "floor_plan_file", "floor_plan_type",
            "has_attachment", "owner", "status", "created_at", "submittedAt",
            "updated_at",
        ]
        read_only_fields = ["owner", "status"]

    def get_has_attachment(self, obj):
        return bool(obj.floor_plan_path)


class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True, default="")
    # 兼容管理端原表格字段口径：customer=客户名、delivery=预计交付、amount=预算金额
    customer = serializers.SerializerMethodField()
    delivery = serializers.CharField(source="delivery_date", read_only=True)
    amount = serializers.CharField(source="budget", read_only=True)

    def get_customer(self, obj):
        return obj.customer.name if obj.customer else ""

    class Meta:
        model = Order
        fields = [
            "id", "order_no", "customer", "customer_name", "project",
            "designer", "budget", "amount", "stage", "status", "delivery",
            "delivery_date", "created_at", "updated_at",
        ]
