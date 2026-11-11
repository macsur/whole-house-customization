# API 路由：客户端真数据 + 管理端统一入口
from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    # 目录类（公开只读）
    path("products", views.ProductViewSet.as_view({"get": "list"}), name="products"),
    path("product", views.product_detail, name="product"),
    path("cases", views.CaseViewSet.as_view({"get": "list"}), name="cases"),
    path("case", views.case_detail, name="case"),
    # 客户端需求提交（游客可提交；multipart 版支持户型图附件）
    path("customize", views.submit_requirement, name="customize"),
    path("requirements", views.submit_requirement_multipart, name="requirements-multipart"),
    # 管理端附件查看/下载（E1）
    path("floorplan", views.admin_floor_plan_download, name="admin-floorplan"),
    # 客户端订单与个人资料
    path("orders", views.client_orders, name="client-orders"),
    path("order", views.client_order_detail, name="client-order"),
    path("profile", views.client_profile, name="client-profile"),
    # 客户端登录/注册（客户端账号体系，密码走 Django 哈希）
    path("login", views.client_login, name="client-login"),
    path("register", views.client_register, name="client-register"),
    # 客服助手（一期静态口径回答，不落库）
    path("assistant", views.assistant_reply, name="assistant"),
    # 管理端（真登录）
    path("admin/login", views.admin_login, name="admin-login"),
    path("entities", views.admin_entities, name="admin-entities"),
    path("requirement", views.admin_requirement_update, name="admin-requirement"),
    path("entity", views.admin_entity_update, name="admin-entity"),
]
