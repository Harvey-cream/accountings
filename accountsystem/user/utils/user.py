from ..models import User
from .jwt_token import verify_token

def get_current_user(request):
    """
    根据请求头中的 Token 获取当前登录的用户
    """
    token = request.META.get('HTTP_AUTHORIZATION')
    user_id = verify_token(token)
    user = User.objects.filter(id=user_id).first()
    return user
