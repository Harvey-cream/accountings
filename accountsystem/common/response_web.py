from enum import Enum
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from django.http import JsonResponse

# 响应状态码枚举
class WebStatusEnum(Enum):
    SUCCESS = (0, "接口执行成功")
    FAILURE = (1, "服务器内部错误")
    UNAUTHORIZED = (2, "用户未登录")
    DENY = (3, "用户无权访问")
    PARAM_ERROR = (400, "参数错误")
    NOT_FOUND = (404, "资源不存在")

    def __init__(self, code, message):
        self.code = code
        self.message = message

# 构造响应结果
class HttpResult:
    @classmethod
    def success(cls, msg="操作成功", data=None):
        result = {
            'code': WebStatusEnum.SUCCESS.code,
            'msg': msg,
            'success': True
        }
        if data is not None:
            result['data'] = data
        return Response(result, status=HTTP_200_OK)

    @classmethod
    def success_with_data(cls, msg, data):
        result = {
            'code': WebStatusEnum.SUCCESS.code,
            'msg': msg,
            'success': True,
            'data': data
        }
        return Response(result, status=HTTP_200_OK)

    @classmethod
    def fail(cls, msg="操作失败", code=WebStatusEnum.FAILURE.code):
        result = {
            'code': code,
            'msg': msg,
            'success': False
        }
        return Response(result, status=HTTP_200_OK)

    @classmethod
    def fail_with_data(cls, msg, data, code=WebStatusEnum.FAILURE.code):
        result = {
            'code': code,
            'msg': msg,
            'success': False,
            'data': data
        }
        return Response(result, status=HTTP_200_OK)

    @classmethod
    def json_fail(cls, msg="操作失败", code=WebStatusEnum.FAILURE.code, status_code=200):
        """专门为中间件提供的 JsonResponse 失败返回"""
        result = {
            'code': code,
            'msg': msg,
            'success': False
        }
        return JsonResponse(result, status=status_code, json_dumps_params={'ensure_ascii': False})

    @classmethod
    def json_success(cls, msg="操作成功", data=None, status_code=200):
        """专门为中间件提供的 JsonResponse 成功返回"""
        result = {
            'code': WebStatusEnum.SUCCESS.code,
            'msg': msg,
            'success': True
        }
        if data is not None:
            result['data'] = data
        return JsonResponse(result, status=status_code, json_dumps_params={'ensure_ascii': False})
