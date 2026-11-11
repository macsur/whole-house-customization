# seed 管理命令：灌演示数据（幂等，按 name/phone/order_no 去重）
import random

from django.core.management.base import BaseCommand

from api.models import Case, Customer, Order, Product, Requirement

PRODUCTS = [
    {"name": "凡尔赛·整体厨房", "category": "厨房", "style": "现代欧式", "material": "胡桃木 / 岩板", "image": "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=1600&q=85", "description": "以暖白框线与深胡桃木构成克制层次，适合开放式厨房。", "features": ["模块化收纳", "防潮柜体", "静音五金"]},
    {"name": "诺曼底·餐边系统", "category": "餐厅", "style": "现代欧式", "material": "烤漆 / 黄铜", "image": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1400&q=85", "description": "兼顾展示、备餐与小家电收纳的餐边组合。", "features": ["隐藏插座", "玻璃展示", "灯光系统"]},
    {"name": "香榭·衣帽空间", "category": "卧室", "style": "法式简约", "material": "橡木 / 织物", "image": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1400&q=85", "description": "开放与封闭收纳相结合，让衣物陈列更有秩序。", "features": ["分区挂放", "首饰抽屉", "感应灯带"]},
    {"name": "卢瓦尔·电视收纳", "category": "客厅", "style": "现代欧式", "material": "暖白烤漆 / 木饰面", "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=85", "description": "弱化设备存在感，保持客厅立面完整。", "features": ["线缆管理", "设备散热", "展示层板"]},
    {"name": "雅典娜·玄关柜", "category": "玄关", "style": "现代欧式", "material": "实木贴皮 / 石材", "image": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1400&q=85", "description": "在有限进深中组织鞋履、外套和随身物品。", "features": ["换鞋座", "通风鞋柜", "随手置物"]},
    {"name": "枫丹白露·书房", "category": "书房", "style": "法式简约", "material": "深胡桃木 / 金属", "image": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1400&q=85", "description": "完整书墙与工作台一体化设计。", "features": ["整墙书柜", "隐藏走线", "可调层板"]},
]

CASES = [
    {"name": "梧桐公馆 128㎡", "space": "厨房", "style": "现代欧式", "area": "128㎡", "image": "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=1400&q=85", "summary": "暖白护墙与胡桃木岛台平衡明暗关系。"},
    {"name": "云栖府 156㎡", "space": "全屋", "style": "现代欧式", "area": "156㎡", "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=85", "summary": "用统一门型连接玄关、餐厅与客厅收纳。"},
    {"name": "江畔名邸 112㎡", "space": "衣帽间", "style": "法式简约", "area": "112㎡", "image": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1400&q=85", "summary": "低饱和色彩与精细分区提升日常效率。"},
    {"name": "学院路私宅 98㎡", "space": "餐厅", "style": "现代欧式", "area": "98㎡", "image": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1400&q=85", "summary": "一体式餐边柜释放小户型公共空间。"},
]

CUSTOMERS = [
    {"name": "张先生", "phone": "13800008000", "city": "温州市", "status": "跟进中"},
    {"name": "王女士", "phone": "13900006213", "city": "杭州市", "status": "方案中"},
    {"name": "刘女士", "phone": "13600002078", "city": "宁波市", "status": "已成交"},
]

REQUIREMENTS = [
    {"contact": "张先生", "phone": "13800008000", "space": "厨房", "style": "现代欧式", "budget": "8–12 万元", "owner": "未分派", "status": "待受理", "description": "开放式厨房，需要岛台和高柜收纳。", "dimensions": "5200×3600×2750mm", "materials": ["暖白烤漆", "胡桃木", "岩板"]},
    {"contact": "王女士", "phone": "13900006213", "space": "全屋", "style": "法式简约", "budget": "12 万元以上", "owner": "陈思远", "status": "方案中", "description": "玄关、餐边和主卧衣柜统一门型。", "dimensions": "建筑面积 128㎡", "materials": ["象牙白", "浅橡木"]},
    {"contact": "刘女士", "phone": "13600002078", "space": "衣帽间", "style": "现代欧式", "budget": "5–8 万元", "owner": "林晓明", "status": "已受理", "description": "需要长衣区、首饰抽屉与行李箱收纳。", "dimensions": "3400×2800×2700mm", "materials": ["胡桃木", "茶色玻璃"]},
]

ORDERS = [
    {"order_no": "DD20260820001", "project": "温暖原木·开放式厨房", "designer": "林晓明", "stage": "方案设计", "delivery_date": "2026-10-18", "status": "进行中"},
    {"order_no": "DD20260712015", "project": "雅白·玄关与餐边柜", "designer": "陈思远", "stage": "生产中", "delivery_date": "2026-09-28", "status": "进行中"},
    {"order_no": "DD20260305008", "project": "衣帽间收纳系统", "designer": "周清", "stage": "配送安装", "delivery_date": "2026-06-20", "status": "已完成"},
]


class Command(BaseCommand):
    help = "灌入木序定制演示数据（幂等）"

    def handle(self, *args, **options):
        product_count = 0
        for item in PRODUCTS:
            item = dict(item)
            lookup_key = item.pop("name")
            _obj, created = Product.objects.get_or_create(name=lookup_key, defaults=item)
            product_count += int(created)

        case_count = 0
        for item in CASES:
            item = dict(item)
            lookup_key = item.pop("name")
            _obj, created = Case.objects.get_or_create(name=lookup_key, defaults=item)
            case_count += int(created)

        customer_count = 0
        phone_to_customer = {}
        for item in CUSTOMERS:
            item = dict(item)
            phone = item.pop("phone")
            obj, created = Customer.objects.get_or_create(phone=phone, defaults=item)
            phone_to_customer[phone] = obj
            customer_count += int(created)

        requirement_count = 0
        for item in REQUIREMENTS:
            item = dict(item)
            phone = item.pop("phone")
            contact = item.pop("contact")
            space = item.pop("space")
            item["customer"] = phone_to_customer[phone]
            _obj, created = Requirement.objects.get_or_create(
                contact=contact, space=space, defaults=item,
            )
            requirement_count += int(created)

        order_count = 0
        for index, item in enumerate(ORDERS):
            item = dict(item)
            order_no = item.pop("order_no")
            item["customer"] = phone_to_customer[CUSTOMERS[index % len(CUSTOMERS)]["phone"]]
            _obj, created = Order.objects.get_or_create(order_no=order_no, defaults=item)
            order_count += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"seed 完成：新增 产品 {product_count} / 案例 {case_count} / 客户 {customer_count} / "
            f"需求 {requirement_count} / 订单 {order_count}；"
            f"当前总数 产品 {Product.objects.count()}、案例 {Case.objects.count()}、"
            f"客户 {Customer.objects.count()}、需求 {Requirement.objects.count()}、订单 {Order.objects.count()}"
        ))
