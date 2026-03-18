from user.models import User
from .jwt_token import verify_token
import oss2
from django.conf import settings
import uuid
import os

def upload_to_oss(file_obj, folder='avatars'):
    """
    上传文件到阿里云 OSS
    :param file_obj: Django 的文件对象
    :param folder: OSS 上的存储目录
    :return: 文件的完整访问 URL
    """
    try:
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
        # 生成文件名
        ext = os.path.splitext(file_obj.name)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        oss_path = f"{folder}/{filename}"
        
        result = bucket.put_object(oss_path, file_obj)
        
        if result.status == 200:
            return oss_path
        else:
            print(f"OSS 上传失败: status={result.status}")
            return None
            
    except Exception as e:
        print(f"OSS 上传异常: {e}")
        return None

def sign_oss_url(oss_path, expires=3600):
    """
    为 OSS 路径生成带签名的临时访问 URL
    :param oss_path: OSS 上的存储路径 (不含域名，如 avatars/xxx.jpg)
    :param expires: 过期时间 (秒)，默认 1 小时
    :return: 带签名的完整访问 URL
    """
    # 如果路径为空，返回一个默认的头像地址 (可以是 OSS 上的固定默认图，也可以是前端静态图路径)
    if not oss_path:
        # 这里建议返回一个前端能识别的占位图路径，或者您 OSS 上的一张固定默认图
        return "/static/default_avatar.png"
    
    # 如果已经是完整 URL 且不是我们的 OSS 域名，直接返回
    if oss_path.startswith('http') and settings.OSS_BUCKET_NAME not in oss_path:
        return oss_path
    
    # 提取相对路径 (防止数据库里存的是完整路径)
    path = oss_path
    if settings.OSS_URL_PREFIX in path:
        path = path.replace(f"{settings.OSS_URL_PREFIX}/", "")
    elif "aliyuncs.com" in path:
        # 兼容旧的存储方式
        path = path.split('.com/')[-1]

    try:
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
        
        # 生成带签名的 URL
        signed_url = bucket.sign_url('GET', path, expires)
        return signed_url
    except Exception as e:
        print(f"OSS 签名失败: {e}")
        return oss_path

def get_current_user(request):
    """
    根据请求头中的 Token 获取当前登录的用户
    """
    token = request.META.get('HTTP_AUTHORIZATION')
    user_id = verify_token(token)
    user = User.objects.filter(id=user_id).first()
    return user
