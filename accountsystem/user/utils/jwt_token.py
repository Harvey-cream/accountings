import datetime
import logging
import os.path
import jwt

logger = logging.getLogger(__name__)

Base_dir = os.path.dirname(os.path.abspath(__file__))
private_path = os.path.join(Base_dir, "private_key.pem")
public_path = os.path.join(Base_dir, "public_key.pem")

# 读取私钥 (RSA)
with open(private_path, "r") as f:
    PRIVATE_KEY = f.read()

# 读取公钥 (RSA)
with open(public_path, "r") as f:
    PUBLIC_KEY = f.read()

def create_token(user_id, minutes=None):
    """
    使用 RSA 私钥生成 JWT token (RS256)
    """
    if minutes:
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
    else:
        # 默认 1 年
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(days=365)
    
    payload = {
        'user_id': user_id,
        'exp': expiration_time.timestamp()
    }
    
    token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
    # 确保返回字符串
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def verify_token(token):
    """
    使用 RSA 公钥验证 JWT token (RS256)
    """
    if not token:
        return None
    if token.startswith('Bearer '):
        token = token[7:]
    try:
        decoded_payload = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
        return decoded_payload.get('user_id')
    except Exception as e:
        logger.error(f'RSA Token验证失败：{str(e)}')
        return None
