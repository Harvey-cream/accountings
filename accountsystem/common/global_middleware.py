from django.utils.deprecation import MiddlewareMixin
from user.utils.jwt_token import verify_token
from user.models import User
from common.response_web import HttpResult, WebStatusEnum
import logging

logger = logging.getLogger(__name__)

class GlobalMiddleware(MiddlewareMixin):
    """
    全局 JWT 校验与异常处理中间件
    """
    
    WHITE_LIST = [
        '/api/user/login/',
        '/api/user/register/',
        '/api/user/refresh_token/',
        '/api/account/icons/',
    ]

    def process_request(self, request):
        path = request.path
        
        if path in self.WHITE_LIST:
            return None

        # 1. 从 Authorization 头获取 Token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return HttpResult.json_fail("未授权访问，请先登录", code=WebStatusEnum.UNAUTHORIZED.code)

        token = auth_header.split(' ')[1]
        
        # 2. 调用 jwt_token.py 中的 verify_token 进行公钥解密
        user_id = verify_token(token)
        
        if not user_id:
            return HttpResult.json_fail("登录已失效或 Token 错误，请重新登录", code=WebStatusEnum.UNAUTHORIZED.code)

        try:
            # 3. 根据解密出的 user_id 拿到真实的 User 对象
            user = User.objects.get(id=user_id)
            
            # 4. 注入到自定义属性中，避免被 Django 默认中间件重置
            request.user_obj = user
            return None
        except User.DoesNotExist:
            return HttpResult.json_fail("用户不存在", code=WebStatusEnum.NOT_FOUND.code)
        except Exception as e:
            return HttpResult.json_fail(f"身份识别异常: {str(e)}", code=WebStatusEnum.FAILURE.code)

    def process_exception(self, request, exception):
        """处理视图中抛出的异常"""
        logger.error(f"全局异常拦截：{str(exception)}")
        
        # 构造统一的错误返回
        return HttpResult.json_fail(
            msg="服务器内部错误，请稍后再试",
            code=WebStatusEnum.FAILURE.code,
            status_code=500
        )
