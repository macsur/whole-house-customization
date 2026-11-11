# 木序定制 · 全屋定制平台 — 核心业务模型（A 单一期五模型）
# Product / Case / Requirement / Customer / Order
# designers / schemes / production / service / users 为二期范围，暂不落库。
from django.db import models


class Customer(models.Model):
    """客户档案：游客提交需求时自动建档，注册用户落库时关联。"""

    name = models.CharField("称呼", max_length=64)
    phone = models.CharField("联系电话", max_length=20, unique=True)
    city = models.CharField("所在城市", max_length=64, blank=True, default="")
    address = models.CharField("详细地址", max_length=255, blank=True, default="")
    preferred_style = models.CharField("偏好风格", max_length=32, blank=True, default="")
    email = models.EmailField("邮箱", blank=True, default="")
    note = models.TextField("备注", blank=True, default="")
    status = models.CharField("跟进状态", max_length=16, default="跟进中")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "客户"
        verbose_name_plural = "客户"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}（{self.phone}）"


class Product(models.Model):
    """客户端产品系列，管理端可维护发布状态。"""

    name = models.CharField("产品名称", max_length=128)
    category = models.CharField("分类", max_length=32)
    style = models.CharField("风格", max_length=32)
    material = models.CharField("主要材质", max_length=128, blank=True, default="")
    image = models.URLField("主图地址", max_length=512, blank=True, default="")
    description = models.TextField("产品描述", blank=True, default="")
    features = models.JSONField("功能特点", default=list, blank=True)
    status = models.CharField("状态", max_length=16, default="已发布")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "产品"
        verbose_name_plural = "产品"
        ordering = ["id"]

    def __str__(self):
        return self.name


class Case(models.Model):
    """真实案例展示。"""

    name = models.CharField("案例名称", max_length=128)
    space = models.CharField("空间", max_length=32)
    style = models.CharField("风格", max_length=32)
    area = models.CharField("面积", max_length=32, blank=True, default="")
    image = models.URLField("主图地址", max_length=512, blank=True, default="")
    summary = models.TextField("案例简介", blank=True, default="")
    status = models.CharField("状态", max_length=16, default="已发布")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "案例"
        verbose_name_plural = "案例"
        ordering = ["id"]

    def __str__(self):
        return self.name


class Requirement(models.Model):
    """客户定制需求（在线定制表单提交）。"""

    STATUS_CHOICES = [
        ("待受理", "待受理"),
        ("已受理", "已受理"),
        ("方案中", "方案中"),
        ("已关闭", "已关闭"),
    ]

    customer = models.ForeignKey(
        Customer, verbose_name="关联客户", on_delete=models.CASCADE,
        related_name="requirements", null=True, blank=True,
    )
    contact = models.CharField("联系人", max_length=64)
    phone = models.CharField("联系电话", max_length=20)
    space = models.CharField("定制空间", max_length=32)
    house_type = models.CharField("房屋类型", max_length=32, blank=True, default="")
    dimensions = models.CharField("空间尺寸", max_length=128, blank=True, default="")
    style = models.CharField("风格偏好", max_length=32, blank=True, default="")
    materials = models.JSONField("材料偏好", default=list, blank=True)
    budget = models.CharField("预算范围", max_length=32, blank=True, default="")
    delivery_date = models.CharField("期望交付", max_length=32, blank=True, default="")
    description = models.TextField("补充说明", blank=True, default="")
    floor_plan_file = models.CharField("户型图文件名", max_length=255, blank=True, default="")
    floor_plan_path = models.CharField("户型图存储路径", max_length=512, blank=True, default="")
    floor_plan_type = models.CharField("户型图类型", max_length=64, blank=True, default="")
    owner = models.CharField("负责人", max_length=64, default="未分派")
    status = models.CharField("状态", max_length=16, choices=STATUS_CHOICES, default="待受理")
    created_at = models.DateTimeField("提交时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "定制需求"
        verbose_name_plural = "定制需求"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contact}·{self.space}需求"


class Order(models.Model):
    """订单：由需求转化而来。"""

    STAGE_CHOICES = [
        ("需求已提交", "需求已提交"),
        ("方案设计", "方案设计"),
        ("方案确认", "方案确认"),
        ("生产中", "生产中"),
        ("配送安装", "配送安装"),
    ]
    STATUS_CHOICES = [
        ("进行中", "进行中"),
        ("已完成", "已完成"),
        ("已取消", "已取消"),
    ]

    order_no = models.CharField("订单号", max_length=32, unique=True)
    customer = models.ForeignKey(
        Customer, verbose_name="客户", on_delete=models.CASCADE,
        related_name="orders", null=True, blank=True,
    )
    requirement = models.ForeignKey(
        Requirement, verbose_name="来源需求", on_delete=models.SET_NULL,
        related_name="orders", null=True, blank=True,
    )
    project = models.CharField("项目名称", max_length=128)
    designer = models.CharField("设计师", max_length=64, blank=True, default="未分派")
    budget = models.CharField("预算金额", max_length=32, blank=True, default="")
    stage = models.CharField("当前阶段", max_length=16, choices=STAGE_CHOICES, default="需求已提交")
    status = models.CharField("状态", max_length=16, choices=STATUS_CHOICES, default="进行中")
    delivery_date = models.CharField("预计交付", max_length=32, blank=True, default="")
    note = models.TextField("备注", blank=True, default="")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_no
