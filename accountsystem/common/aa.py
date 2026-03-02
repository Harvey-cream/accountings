import re
import json
import time
import uuid
from datetime import datetime

from bb_utils import pvuv
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

from common.logger import printc, printe
from common.utils import is_trading_open
from common.web_response import WebStatusEnum
from deposit.utils.aes_verify import AesUtil
from deposit.utils.get_ip_address import get_client_ip
from spot.settings import HOST
from users.models import User
from users.utils import sm3
from users.utils.jwt_token import verify_jwt, decode_jwt_payload, logger
from users.utils.md5_hash import md5_digest
from users.utils.redis_util import get_redis_connection, get_lock, release_lock
from common.exception import MyException

# 不需要token校验的请求
IGNORED_URLS = [
    '/api/phone_login/',
    '/api/register/',
    '/api/login/',
    '/api/reset_password/',
    '/api/send_sms/',
    '/api/logout/',
    '/api/get_oss_file/',
    "/api/bank_card/ocr/",
    "/api/avatar/get/",
    "/api/fadada/sign_task/callback",
    "/api/default_setting/get/",
    "/api/fadada/return_url/",
    "/api/fadada/return_url/h5/",
    "/api/fadada/free_sign/return_url/",
    "/api/fadada/free_sign/return_url/h5/",
    "/api/proxy/pdf/",
    "/api/fadada/h5/loadByUrl/",
    "/api/fadada/corp_auth/return_url/",

    '/quote/marketdata/',
    '/quote/loadpricedata/',
    '/quote/quotedata/',
    '/quote/real-stockdata/',
    '/quote/custom-marketdata/',
    '/quote/table-config/',
    "/quote/dashboard/",

    '/wxPublic/wxPublicLogin/',
    '/wxPublic/getPublicCode/',
    '/wxPublic/wxPublicCode/',
    '/wxPublic/getMiniCode/',
    "/wxPublic/mini_ReciveView/",

    '/data_setting/agreement/get/',
    '/data_setting/goods-detail-info/',
    '/data_setting/trade-status/',
    "/data_setting/trade-period/",
    "/data_setting/faq/",
    "/data_setting/home_notice/",
    "/data_setting/product_info/",
    "/data_setting/dialog/get/",
    "/data_setting/get_deadline/",
    "/data_setting/agreement/fill/",
    "/data_setting/banner/get/",
    "/data_setting/get_version/",
    "/data_setting/get_trade_goods/",
    "/data_setting/get_address_mini/",
    "/data_setting/get_address_mini/recycle/",
    "/data_setting/get_address_mini/room/",
    "/data_setting/guide/types/get/",

    '/recycle/rule/',
    '/stocks/processing/',
    '/recycle/rule/',
    "/deposit/get_deposit_ss/",
    '/deposit/sheng_pay/payment/callback/',
    '/deposit/get_deposit_ss/',
    '/deposit/sheng_wechat_redirect/',

    "/operatelog/order/",

    "/express/callback/",
    "/express/pollcallback/",

    "/help_center/faq/",
    "/help_center/recycle_guide/",

    "/favicon.ico",
    "/api/fadada/h5/loadByUrl/",
    
    "/order/qrcode/store_recycle/",  # 到店回收-扫描二维码

    "/order/qrcode/store_recycle/call_number/",
    
    "/public/get_h5_base_url/",

    # 中金回调
    "/zj/callback/recharge_callback/",
    "/zj/callback/pay_callback/",
    "/zj/callback/sign_callback/",

    "/stocks/get_location/"
]

# 不需要重复校验的请求
IGNORED_REDO_URLS = [
    '/api/refresh/', '/api/enterprise/upload/', '/deposit/get_float_deposit/', '/data_setting/price_popup_setting/',
    '/api/order_setting/get/', '/public/upload_file/', '/deposit/pay_deposit/', "/api/settle_permission/get/",
    '/rbac/user/permissions/', '/customer_service/chat/send_message/' # todo:先放行,后续调整
    '/rbac/user/permissions/', # todo:先放行,后续调整

    # 客服聊天相关
    '/customer_service/chat/send_message/',
    '/customer_service/chat/get_messages/',
    '/customer_service/chat/cs_reply/',
    '/customer_service/chat/cs_get_messages/',
    '/customer_service/chat/recall_message/',
    '/customer_service/chat/cs_send_welcome_at/',
    '/customer_service/chat/update_last_read/',
    '/customer_service/chat/check_message_status/',
    # 回收列表与出入库列表
    '/order/inventory/recycle_cards/',
    '/order/inventory/cards/'
]

# 盛付通回调URL
SHENG_PAY_URLS = [
    '/deposit/sheng_pay/open_account/callback/',
    '/deposit/sheng_pay/separate_account/callback/',
    # '/deposit/sheng_pay/payment/callback/',
    '/deposit/sheng_pay/withdraw/callback/'
]

# 未营业的接口限制
OFF_BUSINESS_URLS = [
    '/order/create/',
    '/order/settle_multi_orders/',
    '/order/settle_single_order/',
    # '/deposit/supply_deposit/',
]

# 需要用户认证的接口
REQUIRE_AUTH_URLS = [
    '/deposit/',
    '/order/',
    '/express/'
]

IGNORE_AUTH_URLS = [
    '/deposit/sheng_pay_liveness/'
]

# 商城调用API
MALL_AUTH_URLS = [
    '/api/check_auth/'
]

MANAGED_IGNORE_URLS = [
	'/api/refresh/',
	'/api/update_user/',
	'/deposit/get_depositrecord/',
	'/order/inventory/cards/'
]


class GlobalMiddleware(MiddlewareMixin):

    def is_whitelist_url(self, path):
        """检查是否为白名单URL"""
        if path in IGNORED_URLS:
            return True
        if path in SHENG_PAY_URLS:
            return True
        return False

    def requires_authentication(self, path, method):
        """检查接口是否需要用户认证"""
        # 白名单接口不需要认证
        if self.is_whitelist_url(path):
            return False

        # GET请求不做要认证检查
        if method == 'GET':
            return False

        # 忽略认证的接口
        for ignore_prefix in IGNORE_AUTH_URLS:
            if path.startswith(ignore_prefix):
                return False

        # 检查是否为需要认证的接口
        for auth_prefix in REQUIRE_AUTH_URLS:
            if path.startswith(auth_prefix):
                return True

        return False

    def check_user_authentication(self, request):
        """检查用户认证状态"""
        user = getattr(request, '_current_user', None)
        if not user:
            return self.get_error_response(status.HTTP_401_UNAUTHORIZED, '当前用户不存在')

        # 金库项目：上传身份证后即视为已认证
        appid = request.headers.get('APPID', '')
        if appid == 'wxddde2ee84641ac77':
            if user.auth_step and user.auth_step != 'upload_idcard':
                return True
        # 检查用户是否已认证
        if not user.is_authenticated:
            return self.get_error_response(status.HTTP_403_FORBIDDEN, '用户未认证，请前往认证')

        return True

    # 对所有请求进行拦截处理
    def process_request(self, request):

        if request.path in MALL_AUTH_URLS:
            token = request.META.get('HTTP_AUTHORIZATION')
            if token == sm3.digestHex(HOST):
                return None
            else:
                return self.get_error_response(status.HTTP_403_FORBIDDEN, '无权访问')

        # 判断非交易时间
        if request.path in OFF_BUSINESS_URLS:
            if not is_trading_open():
                return self.get_error_response(status.HTTP_403_FORBIDDEN, '非交易时间，禁止操作')

        # 不需要进行token校验的请求，直接放行
        if IGNORED_URLS.__contains__(request.path):
            printc(f"放行无需校验的请求，客户端IP：{get_client_ip(request)}，请求路径：{request.path}")
            return None

        managed_user_id = request.headers.get('X-Managed-User-ID')
        if managed_user_id and request.method != 'GET' and request.path not in MANAGED_IGNORE_URLS:
            return self.get_error_response(status.HTTP_403_FORBIDDEN, '无权操作其他用户信息')

        # 盛付通回调请求
        if SHENG_PAY_URLS.__contains__(request.path):
            printc(f"放行盛付通请求，客户端IP：{get_client_ip(request)}，请求路径：{request.path}")
            if 'ticket' in request.GET:
                ticket = request.GET['ticket']
                result = AesUtil.decrypt(ticket)
                if result:
                    result = json.loads(result)
                    now = datetime.now()
                    current_mills = int(now.timestamp() * 1000)
                    if current_mills <= result['expires']:
                        return None
                    else:
                        return self.get_error_response(status.HTTP_403_FORBIDDEN, '接口访问过期')
            return self.get_error_response(status.HTTP_403_FORBIDDEN, '用户无权访问')

        printc(f"客户端IP：{get_client_ip(request)}，请求路径：{request.path}")

        # 判断是否重复请求
        try:
            # 如果是刷新token请求，则进行判断
            if request.path == '/api/refresh/':
                req_body = json.loads(request.body)
                if req_body is None or req_body == '':
                    return self.get_error_response(status.HTTP_400_BAD_REQUEST, 'refresh_token不能为空')

                # refresh_token无效，无法解析出内容
                refresh_token = req_body.get('token')
                user_id = verify_jwt(refresh_token)
                if user_id is None:
                    return self.get_error_response(status.HTTP_401_UNAUTHORIZED, 'refresh_token无效')

                # redis中的token是否过期
                user = User.objects.filter(id=user_id, is_deleted=False).first()
                if user is not None:
                    try:
                        redis_conn = get_redis_connection()
                        key = f"refresh_token:{user_id}:{md5_digest(refresh_token)}"
                        ttl_seconds = redis_conn.ttl(key)
                        if ttl_seconds == -2:
                            return self.get_error_response(status.HTTP_401_UNAUTHORIZED, '请重新登录')
                    except Exception as redis_e:
                        logger.error(f'Redis连接失败：{redis_e}')
                        # Redis异常时跳过token检查，允许请求继续
                        pass
                    if not user.is_enable:
                        return self.get_error_response(status.HTTP_401_UNAUTHORIZED, '网络错误，请联系客服')
                    managed_user_id = request.headers.get('X-Managed-User-ID')
                    if managed_user_id:
                        request._current_user = User.objects.filter(id=managed_user_id, is_deleted=False).first()
                    else:
                        request._current_user = user  # 在SpotConfig加载current_user
                else:
                    return self.get_error_response(status.HTTP_401_UNAUTHORIZED, '用户不存在')

            else:
                # 请求是否携带token
                token = request.META.get('HTTP_AUTHORIZATION')
                if token is None or token == '':
                    return self.get_error_response(status.HTTP_403_FORBIDDEN, '用户无权访问')

                # token无效，无法解析出内容
                user_id = verify_jwt(token)
                if user_id is None:
                    return self.get_error_response(status.HTTP_401_UNAUTHORIZED, 'token无效')

                # redis中的token是否过期
                user = User.objects.filter(id=user_id, is_deleted=False).first()
                if user is not None:
                    try:
                        redis_conn = get_redis_connection()
                        key = 'token:' + user.mobile + ":" + md5_digest(token)
                        ttl_seconds = redis_conn.ttl(key)
                        if ttl_seconds == -2:
                            return self.get_error_response(status.HTTP_401_UNAUTHORIZED, '用户验证失败，请重新登录')
                    except Exception as redis_e:
                        logger.error(f'Redis连接失败：{redis_e}')
                        # Redis异常时跳过token检查，允许请求继续
                        pass
                    if not user.is_enable:
                        return self.get_error_response(status.HTTP_401_UNAUTHORIZED, '网络错误，请联系客服')

                    managed_user_id = request.headers.get('X-Managed-User-ID')
                    if managed_user_id:
                        request._current_user = User.objects.filter(id=managed_user_id, is_deleted=False).first()
                    else:
                        request._current_user = user  # 在SpotConfig加载current_user

                    # 解析 token 获取 staff_user_id (企业员工登录时存在)
                    token_payload = decode_jwt_payload(token)
                    if token_payload and 'staff_user_id' in token_payload:
                        request._staff_user_id = token_payload['staff_user_id']
                    else:
                        request._staff_user_id = None

            # 检查用户认证状态
            if self.requires_authentication(request.path, request.method):
                auth_result = self.check_user_authentication(request)
                if auth_result is not True:
                    return auth_result

            # 重复请求处理 - 只对非GET请求进行防重
            if request.path not in IGNORED_REDO_URLS and request.method != 'GET':
                # 构建请求唯一标识
                request_identifier = self._build_request_identifier(request)

                if request_identifier:
                    lock_key = f"reqLock:{user_id}:{request.path}:{request_identifier}"
                    lock_value = str(uuid.uuid4())
                    # 锁定时间设置为1秒，防止短时间内重复请求，让锁自然过期
                    lock_acquired = get_lock(lock_key, lock_value, 1)
                    if not lock_acquired:
                        return self.get_error_response(status.HTTP_429_TOO_MANY_REQUESTS, '操作过快，请勿重复提交')
                    # 将锁信息存储到request中，用于后续释放
                    request._lock_key = lock_key
                    request._lock_value = lock_value

        except Exception as e:
            logger.error(f'token校验失败：{e}')
            return self.get_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, '服务器内部错误')

        return None  # 继续处理

    def _build_request_identifier(self, request):
        """构建请求唯一标识"""
        try:
            # 只处理需要防重的请求方法
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                # POST等请求使用请求体
                if request.body == b'':
                    request_data = {}
                elif request.content_type and 'multipart/form-data' in request.content_type:
                    # 文件上传请求，使用POST参数
                    request_data = dict(request.POST.items())
                else:
                    try:
                        utf8_body = request.body.decode('utf-8')
                        request_data = json.loads(utf8_body)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        # 如果无法解析JSON，使用原始body的hash
                        return md5_digest(request.body.decode('utf-8', errors='ignore'))

                return md5_digest(json.dumps(request_data, sort_keys=True))

            else:
                # 其他请求方法（理论上不会到这里，因为GET已经被过滤）
                return md5_digest(f"{request.method}:{request.path}")

        except Exception as e:
            logger.error(f'构建请求标识失败：{e}')
            # 发生异常时返回基础标识
            return md5_digest(f"{request.method}:{request.path}:{int(time.time())}")

    def process_response(self, request, response):
        """在响应返回前处理锁"""
        if hasattr(request, '_lock_key') and hasattr(request, '_lock_value'):
            # 正常情况下不释放锁，让锁自然过期来防止短时间内的重复请求
            if response.status_code >= 500:
                release_lock(request._lock_key, request._lock_value)
        return response

    # 返回错误的响应信息
    def get_error_response(self, code, msg):
        return HttpResponse(
            json.dumps({'code': code, 'msg': msg, 'success': False}, ensure_ascii=False),
            status=code,
            content_type='application/json'
        )

    def process_exception(self, request, exception):
        """处理视图中抛出的异常"""
        if isinstance(exception, MyException):
            result = {
                'code': exception.code,
                'msg': exception.msg,
                'success': False
            }
            return JsonResponse(result, status=exception.status_code, json_dumps_params={'ensure_ascii': False})

        printe(f"异常：{exception}")
        # 获取接口路径（不包含URL参数）
        path = self._clean_path(request.path)
        pvuv(
            app="mini_app_err",
            key=f"{path}##{str(exception)[:100]}".replace(",", "，"),  # 因为","是pvuv解析的特殊字符
            uv=self._get_user_id(request)
        )
        result = {
            'code': WebStatusEnum.FAILURE.code,
            'msg': WebStatusEnum.FAILURE.message,
            'success': False
        }
        return JsonResponse(result, status=500, json_dumps_params={'ensure_ascii': False})

    def _get_user_id(self, request):
        """
        获取用户ID
        优先从request._current_user获取，如果没有则返回default
        """
        try:
            # 从中间件设置的当前用户获取ID
            if hasattr(request, '_current_user') and request._current_user:
                return str(request._current_user.id)

            # 如果没有用户信息，返回default
            return "default"

        except Exception:
            return "default"

    def _clean_path(self, path):
        """
        清理路径，移除URL参数和多余信息
        例如: /api/user/123/ -> /api/user
        """
        # 移除查询参数
        if '?' in path:
            path = path.split('?')[0]

        # 移除路径中的数字ID（常见的RESTful API模式）
        # 例如: /api/user/123/ -> /api/user/
        path = re.sub(r'/\d+/', '/', path)

        # 移除末尾的斜杠（除了根路径）
        if path != '/' and path.endswith('/'):
            path = path[:-1]

        return path
