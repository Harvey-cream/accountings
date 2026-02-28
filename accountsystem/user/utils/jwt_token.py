import datetime
import logging
import os.path
import jwt

logger = logging.getLogger(__name__)

Base_dir = os.path.dirname(os.path.abspath(__file__))
private_path = os.path.join(Base_dir,"private_key.pem")
public_path = os.path.join(Base_dir,"public_key.pem")

# 读取私钥
with open(private_path, "r") as f:
    PRIVATE_KEY = f.read()

# 读取公钥
with open(public_path, "r") as f:
    PUBLIC_KEY = f.read()

def create_token(user_id):
    """
    使用私钥生成 JWT token
    :param user_id: 用户唯一标识
    :param timeout: 有效期 (小时)
    :return: token 字符串
    """
    # 根据参数设置过期时间
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=365 * 24 * 60)
    
    payload = {
        'user_id': user_id,
        'exp': expiration_time.timestamp()
    }
    

    return jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')

def verify_token(token):
    if token is None:
        return None
    if token.startswith('Bearer '):
        token = token[7:]
    try:
        decoded_payload = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
        return decoded_payload['user_id']
    except Exception as e:
        logger.error(f'token验证失败：{e}')
        return None
