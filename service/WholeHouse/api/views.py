# 木序定制 · 全屋定制平台 — REST API 视图（A 单一期）
# 统一信封 {code, message, data}，列表 items/total。
# 游客可读目录类接口与提交需求；管理端写接口需真登录（DRF Token，按 is_staff 分角色）。
import random
import re
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Case, Customer, Order, Product, Requirement
from .serializers import (
    CaseSerializer,
    CustomerSerializer,
    OrderSerializer,
    ProductSerializer,
    RequirementSerializer,
)


def _mask_phone(phone):
    """手机号脱敏：保留前 3 后 4。"""
    if phone and len(phone) >= 7:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone or ""


def _get_or_create_customer(contact, phone, city="", preferred_style=""):
    """按手机号幂等建档：有则复用、无则建。"""
    customer, _created = Customer.objects.get_or_create(
        phone=phone,
        defaults={"name": contact, "city": city, "preferred_style": preferred_style},
    )
    return customer


def _gen_order_no():
    """生成订单号：DD + 日期 + 四位随机序号。"""
    today = datetime.now().strftime("%Y%m%d")
    return f"DD{today}{random.randint(1000, 9999)}"


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response(
        {
            "code": 200,
            "message": "success",
            "data": {"status": "ok", "service": "whole-house-api"},
        }
    )


# ---------------- 客户端账号体系 ----------------


@api_view(["POST"])
@permission_classes([AllowAny])
def client_register(request):
    """客户端注册：手机号 + 密码（Django 哈希存储），并幂等关联 Customer 档案。

    关联口径：Django User.username = 手机号；Customer.phone = 手机号。
    注册即建 Customer（昵称落 Customer.name），后续需求/订单经手机号关联。
    """
    payload = request.data or {}
    phone = str(payload.get("phone") or "").strip()
    password = str(payload.get("password") or "")
    name = str(payload.get("name") or "").strip() or "客户"

    if not re.fullmatch(r"1\d{10}", phone):
        return Response({"code": 400, "message": "手机号格式不正确", "data": None})
    if len(password) < 6:
        return Response({"code": 400, "message": "密码至少 6 位", "data": None})
    if User.objects.filter(username=phone).exists():
        return Response({"code": 409, "message": "该手机号已注册", "data": None})

    with transaction.atomic():
        user = User.objects.create_user(
            username=phone, password=password, first_name=name, is_staff=False,
        )
        Customer.objects.get_or_create(phone=phone, defaults={"name": name})
        from rest_framework.authtoken.models import Token

        token = Token.objects.create(user=user)

    return Response({
        "code": 200, "message": "success",
        "data": {"id": user.pk, "token": token.key, "name": name, "phone": _mask_phone(phone)},
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def client_login(request):
    """客户端登录：手机号 + 密码换 DRF Token（客户端账号 is_staff=False，无法调管理端写接口）。"""
    payload = request.data or {}
    phone = str(payload.get("phone") or "").strip()
    password = str(payload.get("password") or "")
    if not phone or not password:
        return Response({"code": 400, "message": "请输入手机号和密码", "data": None})

    user = User.objects.filter(username=phone, is_staff=False).first()
    if user is None or not user.check_password(password):
        return Response({"code": 401, "message": "手机号或密码不正确", "data": None})

    from rest_framework.authtoken.models import Token

    token, _created = Token.objects.get_or_create(user=user)
    return Response({
        "code": 200, "message": "success",
        "data": {"token": token.key, "name": user.first_name or "客户", "phone": _mask_phone(phone)},
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def client_order_detail(request):
    """客户端订单详情：登录后校验归属，未登录返回 401。"""
    user = getattr(request, "user", None)
    order_id = request.query_params.get("id")
    if not (getattr(user, "is_authenticated", False) and not user.is_staff):
        return Response({"code": 401, "message": "请先登录", "data": None})
    customer = Customer.objects.filter(phone=user.username).first()
    order = Order.objects.filter(pk=order_id, customer=customer).first()
    if order is None:
        return Response({"code": 404, "message": "未找到对应订单", "data": None})
    return Response({"code": 200, "message": "success", "data": OrderSerializer(order).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def assistant_reply(request):
    """客服助手：一期沿用静态口径回答，不落库。"""
    from .assistant import answer_for

    message = str((request.data or {}).get("message") or "")
    return Response({"code": 200, "message": "success", "data": {"message": answer_for(message)}})


# ---------------- 目录类（公开只读） ----------------


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """客户端产品系列。"""

    queryset = Product.objects.filter(status="已发布")
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [OrderingFilter]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        style = self.request.query_params.get("style")
        if category:
            queryset = queryset.filter(category=category)
        if style:
            queryset = queryset.filter(style=style)
        return queryset

    @action(detail=False, methods=["get"], url_path="")
    def list_root(self, request):
        return self.list(request)


class CaseViewSet(viewsets.ReadOnlyModelViewSet):
    """客户端真实案例。"""

    queryset = Case.objects.filter(status="已发布")
    serializer_class = CaseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        space = self.request.query_params.get("space")
        style = self.request.query_params.get("style")
        if space:
            queryset = queryset.filter(space=space)
        if style:
            queryset = queryset.filter(style=style)
        return queryset


@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail(request):
    """客户端产品详情：?id=xx。"""
    item = Product.objects.filter(pk=request.query_params.get("id")).first()
    if item is None:
        return Response({"code": 404, "message": "未找到产品", "data": None})
    return Response({"code": 200, "message": "success", "data": ProductSerializer(item).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def case_detail(request):
    """客户端案例详情：?id=xx。"""
    item = Case.objects.filter(pk=request.query_params.get("id")).first()
    if item is None:
        return Response({"code": 404, "message": "未找到案例", "data": None})
    return Response({"code": 200, "message": "success", "data": CaseSerializer(item).data})


# ---------------- 需求（游客可提交，管理端需登录改） ----------------


@api_view(["POST"])
@permission_classes([AllowAny])
def submit_requirement(request):
    """客户端在线定制提交需求（游客可提交，幂等建档客户）。

    body 字段与原静态表单一致：contact/phone/space/houseType/dimensions/
    style/materials/budget/deliveryDate/description/floorPlan
    """
    payload = request.data or {}
    contact = str(payload.get("contact") or "").strip()
    phone = str(payload.get("phone") or "").strip()
    space = str(payload.get("space") or "").strip()

    errors = {}
    if not contact:
        errors["contact"] = "请填写联系人"
    if not re.fullmatch(r"1\d{10}", phone):
        errors["phone"] = "请输入正确的 11 位手机号"
    if not space:
        errors["space"] = "请选择定制空间"
    if errors:
        return Response({"code": 400, "message": "；".join(errors.values()), "data": None})

    dims = payload.get("dimensions") or {}
    dimensions = (
        f"{dims.get('length', '')}×{dims.get('width', '')}×{dims.get('height', '')}mm"
        if isinstance(dims, dict) and dims.get("length")
        else str(payload.get("dimensions") or "")
    )

    # 关联已登录客户端账号的客户身份（E 单接入后自动生效）；游客提交建独立档案
    customer = None
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False) and not user.is_staff:
        customer, _created = Customer.objects.get_or_create(
            phone=user.username,
            defaults={"name": contact or user.first_name or "客户"},
        )

    with transaction.atomic():
        requirement = Requirement.objects.create(
            customer=customer,
            contact=contact,
            phone=phone,
            space=space,
            house_type=str(payload.get("houseType") or ""),
            dimensions=dimensions,
            style=str(payload.get("style") or ""),
            materials=payload.get("materials") or [],
            budget=str(payload.get("budget") or ""),
            delivery_date=str(payload.get("deliveryDate") or ""),
            description=str(payload.get("description") or ""),
            floor_plan_file=str(payload.get("floorPlan") or ""),
        )
        if customer is None:
            customer = _get_or_create_customer(contact, phone)
            requirement.customer = customer
            requirement.save(update_fields=["customer"])

    data = RequirementSerializer(requirement).data
    return Response({"code": 200, "message": "success", "data": {"id": requirement.pk, **data}})


@api_view(["POST"])
@permission_classes([AllowAny])
def submit_requirement_multipart(request):
    """客户端在线定制提交需求——multipart 版（E1）。

    表单字段与 JSON 版一致；额外支持 floorPlan 附件字段（jpg/png/webp/PDF，≤10MB）。
    附件存 WHC_MEDIA_ROOT 持久卷（compose 卷 whc-media），容器重建不丢。
    """
    from .attachments import save_floor_plan, validate_floor_plan

    payload = {key: value for key, value in request.data.items() if key != "floorPlan"}
    upload = request.FILES.get("floorPlan")

    # 复用 JSON 版校验逻辑：request.data 里已是字符串，转成同一结构再校验
    import json as _json

    try:
        materials = _json.loads(payload.get("materials", "[]")) if isinstance(payload.get("materials"), str) else (payload.get("materials") or [])
        dimensions_raw = payload.get("dimensions")
        dims = _json.loads(dimensions_raw) if isinstance(dimensions_raw, str) else (dimensions_raw or {})
    except (ValueError, TypeError):
        return Response({"code": 400, "message": "materials 或 dimensions 字段格式不正确", "data": None})

    contact = str(payload.get("contact") or "").strip()
    phone = str(payload.get("phone") or "").strip()
    space = str(payload.get("space") or "").strip()

    errors = {}
    if not contact:
        errors["contact"] = "请填写联系人"
    if not re.fullmatch(r"1\d{10}", phone):
        errors["phone"] = "请输入正确的 11 位手机号"
    if not space:
        errors["space"] = "请选择定制空间"
    if errors:
        return Response({"code": 400, "message": "；".join(errors.values()), "data": None})

    try:
        ext, content_type = validate_floor_plan(upload)
    except ValueError as exc:
        return Response({"code": 400, "message": str(exc), "data": None})

    dims = dims if isinstance(dims, dict) else {}
    dimensions = (
        f"{dims.get('length', '')}×{dims.get('width', '')}×{dims.get('height', '')}mm"
        if dims.get("length")
        else str(dimensions_raw or "")
    )

    customer = None
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False) and not user.is_staff:
        customer, _created = Customer.objects.get_or_create(
            phone=user.username,
            defaults={"name": contact or user.first_name or "客户"},
        )

    with transaction.atomic():
        floor_plan_rel_path, _saved_name = ("", "")
        if upload is not None:
            floor_plan_rel_path, _saved_name = save_floor_plan(
                upload, upload.name, ext, content_type,
            )
        requirement = Requirement.objects.create(
            customer=customer,
            contact=contact,
            phone=phone,
            space=space,
            house_type=str(payload.get("houseType") or ""),
            dimensions=dimensions,
            style=str(payload.get("style") or ""),
            materials=materials,
            budget=str(payload.get("budget") or ""),
            delivery_date=str(payload.get("deliveryDate") or ""),
            description=str(payload.get("description") or ""),
            floor_plan_file=str(upload.name) if upload else "",
            floor_plan_path=floor_plan_rel_path,
            floor_plan_type=content_type or "",
            floor_plan_size=upload.size if upload else 0,
        )
        if customer is None:
            customer = _get_or_create_customer(contact, phone)
            requirement.customer = customer
            requirement.save(update_fields=["customer"])

    data = RequirementSerializer(requirement).data
    return Response({"code": 200, "message": "success", "data": {"id": requirement.pk, **data}})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_floor_plan_download(request):
    """管理端查看/下载需求附件（需真登录）。/api/floorplan?requirement=<id>"""
    if not _staff_required(request):
        return Response({"code": 403, "message": "需要管理端登录", "data": None})
    requirement = Requirement.objects.filter(pk=request.query_params.get("requirement")).first()
    if requirement is None or not requirement.floor_plan_path:
        return Response({"code": 404, "message": "附件不存在", "data": None})

    import os as _os

    from django.http import FileResponse

    full_path = _os.path.join(attachments_media_root(), requirement.floor_plan_path)
    if not _os.path.isfile(full_path):
        return Response({"code": 404, "message": "附件文件已丢失", "data": None})
    return FileResponse(
        open(full_path, "rb"),
        as_attachment=bool(request.query_params.get("download")),
        filename=requirement.floor_plan_file or None,
        content_type=requirement.floor_plan_type or "application/octet-stream",
    )


def attachments_media_root():
    from .attachments import media_root

    return media_root()


# ---------------- 管理端（真登录校验） ----------------


def _staff_required(request):
    return bool(getattr(request, "user", None) and request.user.is_authenticated and request.user.is_staff)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def admin_login(request):
    """管理端登录换 DRF Token（沿用 DRF authtoken 体系）。"""
    from rest_framework.authtoken.models import Token

    if request.method == "GET":
        return Response({"code": 200, "message": "success", "data": {"ok": True}})

    account = str((request.data or {}).get("account") or "").strip()
    password = str((request.data or {}).get("password") or "")
    if not account or not password:
        return Response({"code": 400, "message": "请输入账号和密码", "data": None})

    # 站主只许「创建方法」层面写密码，此处走 Django 认证后端（check_password），不落明文日志
    user = User.objects.filter(username=account).first()
    if user is None or not user.check_password(password):
        return Response({"code": 401, "message": "账号或密码不正确", "data": None})
    if not user.is_staff:
        return Response({"code": 403, "message": "该账号无管理端权限", "data": None})

    token, _created = Token.objects.get_or_create(user=user)
    return Response({"code": 200, "message": "success", "data": {"token": token.key}})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_entities(request):
    """管理端列表统一入口：?entity=requirements|customers|products|cases|orders"""
    entity = request.query_params.get("entity", "")
    keyword = request.query_params.get("keyword", "").strip()
    status_filter = request.query_params.get("status", "").strip()

    mapping = {
        "requirements": (Requirement.objects.all(), RequirementSerializer),
        "customers": (Customer.objects.all(), CustomerSerializer),
        "products": (Product.objects.all(), ProductSerializer),
        "cases": (Case.objects.all(), CaseSerializer),
        "orders": (Order.objects.all(), OrderSerializer),
    }
    if entity in ("designers", "schemes", "production", "service", "users"):
        # 二期实体：一期未落库，返回空列表让前端渲染占位（交付帖逐项标注「仍静态」）。
        return Response({"code": 200, "message": "success", "data": {"items": [], "total": 0}})
    if entity not in mapping:
        return Response({"code": 400, "message": f"未知实体：{entity}", "data": None})
    if not _staff_required(request):
        return Response({"code": 403, "message": "需要管理端登录", "data": None})

    queryset, serializer_class = mapping[entity]
    items_queryset = list(queryset)
    if keyword:
        items_queryset = [
            obj for obj in items_queryset
            if keyword in str(serializer_class(obj).data)
        ]
    if status_filter:
        items_queryset = [obj for obj in items_queryset if getattr(obj, "status", "") == status_filter]

    serializer = serializer_class(items_queryset, many=True)
    items = serializer.data
    return Response({"code": 200, "message": "success", "data": {"items": items, "total": len(items)}})


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def admin_requirement_update(request):
    """管理端查/改需求（详情、受理/分派/状态推进），需真登录。"""
    if not _staff_required(request):
        return Response({"code": 403, "message": "需要管理端登录", "data": None})

    if request.method == "GET":
        requirement = Requirement.objects.filter(pk=request.query_params.get("id")).first()
        if requirement is None:
            return Response({"code": 404, "message": "需求不存在", "data": None})
        return Response({"code": 200, "message": "success", "data": RequirementSerializer(requirement).data})

    payload = request.data or {}
    requirement_id = payload.get("id")
    requirement = Requirement.objects.filter(pk=requirement_id).first()
    if requirement is None:
        return Response({"code": 404, "message": "需求不存在", "data": None})

    allowed = {"owner", "status", "description"}
    for field in allowed:
        if field in payload:
            setattr(requirement, field, payload[field])
    requirement.save()
    return Response({"code": 200, "message": "success", "data": RequirementSerializer(requirement).data})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def admin_entity_update(request):
    """管理端通用实体更新（方案审核/发布状态等场景，一期覆盖 products/cases/orders/customers）。"""
    if not _staff_required(request):
        return Response({"code": 403, "message": "需要管理端登录", "data": None})
    payload = request.data or {}
    entity = payload.get("entity", "")
    entity_id = payload.get("id")
    mapping = {
        "products": (Product, ProductSerializer),
        "cases": (Case, CaseSerializer),
        "orders": (Order, OrderSerializer),
        "customers": (Customer, CustomerSerializer),
        "requirements": (Requirement, RequirementSerializer),
    }
    if entity not in mapping:
        return Response({"code": 400, "message": f"未知实体：{entity}", "data": None})

    model, serializer_class = mapping[entity]
    obj = model.objects.filter(pk=entity_id).first()
    if obj is None:
        return Response({"code": 404, "message": "对象不存在", "data": None})

    for field, value in payload.items():
        if field in {"entity", "id"}:
            continue
        if hasattr(obj, field):
            setattr(obj, field, value)
    obj.save()
    return Response({"code": 200, "message": "success", "data": serializer_class(obj).data})


# ---------------- 客户端个人/订单（游客兜底演示数据，登录后真数据） ----------------


@api_view(["GET"])
@permission_classes([AllowAny])
def client_orders(request):
    """客户端订单列表：登录的客户端用户看自己的订单，未登录返回空列表。"""
    user = getattr(request, "user", None)
    items = []
    total = 0
    if getattr(user, "is_authenticated", False) and not user.is_staff:
        customer = Customer.objects.filter(phone=user.username).first()
        if customer:
            queryset = Order.objects.filter(customer=customer)
            status_filter = request.query_params.get("status")
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            data = OrderSerializer(queryset, many=True).data
            items, total = data, len(data)
    return Response({"code": 200, "message": "success", "data": {"items": items, "total": total}})


@api_view(["GET", "PUT"])
@permission_classes([AllowAny])
def client_profile(request):
    """客户端个人资料：登录后返回真资料，未登录返回匿名占位。"""
    user = getattr(request, "user", None)
    customer = None
    if getattr(user, "is_authenticated", False) and not user.is_staff:
        customer = Customer.objects.filter(phone=user.username).first()

    if request.method == "PUT":
        if customer is None:
            return Response({"code": 401, "message": "请先登录", "data": None})
        payload = request.data or {}
        for field in ("name", "city", "address", "preferred_style", "email"):
            alias = {"name": "name", "city": "city", "address": "address",
                     "preferredStyle": "preferred_style", "email": "email"}.get(field)
            if alias and alias in payload:
                setattr(customer, field, payload[alias])
        customer.save()
        customer.refresh_from_db()

    if customer is None:
        return Response({
            "code": 200, "message": "success",
            "data": {"name": "游客", "phone": "", "city": "", "address": "", "preferredStyle": ""},
        })
    return Response({
        "code": 200, "message": "success",
        "data": {
            "id": customer.pk, "name": customer.name,
            "phone": _mask_phone(customer.phone), "city": customer.city,
            "address": customer.address, "preferredStyle": customer.preferred_style,
        },
    })
