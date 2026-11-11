# 统一响应信封 {code, message, data}（列表带 items / total）
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList


def _plain(data):
    """把 DRF 返回的 OrderedList/ReturnDict 摊平成原生 list/dict，便于 JSON 渲染。"""
    if isinstance(data, (ReturnDict, dict)):
        return {key: _plain(value) for key, value in data.items()}
    if isinstance(data, (ReturnList, list, tuple)):
        return [_plain(item) for item in data]
    return data


class EnvelopeJSONRenderer(JSONRenderer):
    """统一信封渲染：所有 DRF JSON 响应包成 {code, message, data}。

    分页响应自动拆成 {items, total}；data 里自带 items 的直接透传。
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        status_code = response.status_code if response is not None else 200

        if isinstance(data, dict) and set(data.keys()) == {"code", "message", "data"}:
            envelope = data
        elif isinstance(data, dict) and "results" in data:
            # 分页结果 → items / total
            envelope = {
                "code": status_code,
                "message": "success",
                "data": {
                    "items": _plain(data.get("results", [])),
                    "total": data.get("count", 0),
                },
            }
        elif isinstance(data, dict) and "items" in data and "total" in data:
            envelope = {"code": status_code, "message": "success", "data": _plain(data)}
        else:
            envelope = {"code": status_code, "message": "success", "data": _plain(data)}

        if response is not None and status_code >= 400:
            envelope["code"] = status_code
            envelope["message"] = _error_message(data)
            envelope["data"] = None

        return super().render(envelope, accepted_media_type, renderer_context)


def _error_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            detail = data["detail"]
            return str(detail)
        for value in data.values():
            if isinstance(value, (list, tuple)) and value:
                return str(value[0])
            if isinstance(value, str):
                return str(value)
    return "请求处理失败"
