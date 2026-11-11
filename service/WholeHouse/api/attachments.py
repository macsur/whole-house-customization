# E1：户型图附件存储与校验
# 文件存 WHC_MEDIA_ROOT（compose 持久卷 whc-media，与 MySQL 数据同级）；
# 未设置该环境变量时落 BASE_DIR/media（本地自检），不落容器临时文件系统意义上的易失区。
import os
import uuid

from django.conf import settings

ALLOWED_FLOOR_PLAN_TYPES = {
    "image/jpeg": (".jpg", ".jpeg"),
    "image/png": (".png",),
    "image/webp": (".webp",),
    "application/pdf": (".pdf",),
}
MAX_FLOOR_PLAN_BYTES = 10 * 1024 * 1024  # ≤10MB


def media_root():
    return os.getenv("WHC_MEDIA_ROOT") or str(settings.BASE_DIR / "media")


def validate_floor_plan(file_obj):
    """校验户型图：类型 + 大小。返回 (ext, content_type) 或抛 ValueError（中文报错）。"""
    if file_obj is None:
        return None, None
    content_type = (file_obj.content_type or "").lower()
    if content_type not in ALLOWED_FLOOR_PLAN_TYPES:
        raise ValueError("户型图仅支持 jpg/png/webp 图片或 PDF 文件")
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)
    if size > MAX_FLOOR_PLAN_BYTES:
        raise ValueError("户型图不能超过 10MB")
    if size == 0:
        raise ValueError("户型图文件为空")
    ext = ALLOWED_FLOOR_PLAN_TYPES[content_type]
    return ext, content_type


def save_floor_plan(file_obj, original_name, ext, content_type):
    """把户型图写入持久卷，返回 (相对路径, 保存文件名)。"""
    root = media_root()
    os.makedirs(root, exist_ok=True)
    safe_ext = ext[0] if ext else ".bin"
    saved_name = f"floorplan_{uuid.uuid4().hex}{safe_ext}"
    rel_path = os.path.join("floorplans", saved_name)
    full_dir = os.path.join(root, "floorplans")
    os.makedirs(full_dir, exist_ok=True)
    with open(os.path.join(full_dir, saved_name), "wb") as fh:
        for chunk in file_obj.chunks():
            fh.write(chunk)
    return rel_path, saved_name
