import datetime
import logging
import os.path
import jwt

Base_dir = os.path.dirname(os.path.abspath(__file__))
private_path = os.path.join(Base_dir,"private_key.pem")
public_path = os.path.join(Base_dir,"public_key.pem")

# 读取私钥
with open(private_path, "r") as f:
    PRIVATE_KEY = f.read()

# 读取公钥
with open(public_path, "r") as f:
    PUBLIC_KEY = f.read()

def create_token(user_id, minutes=10, weeks=0, is_refresh=False):
    """
    使用私钥生成 JWT token
    :param user_id: 用户唯一标识
    :param minutes: 过期分钟数
    :param weeks: 过期周数
    :param is_refresh: 是否为刷新令牌
    :return: (token 字符串, 过期时间戳)
    """
    now = datetime.datetime.utcnow()
    # 根据参数设置过期时间
    expiration_time = now + datetime.timedelta(minutes=minutes, weeks=weeks)
    expires_at = int(expiration_time.timestamp())
    
    payload = {
        'user_id': user_id,
        'exp': expires_at,
        'iat': int(now.timestamp()),
        'is_refresh': is_refresh
    }
    
    token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
    return token, expires_at

def verify_token(token, expect_refresh=False):
    """
    使用公钥验证 JWT token
    :param token: token 字符串
    :param expect_refresh: 是否期望验证的是刷新令牌
    :return: 解密后的 payload 或 None
    """
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
        # 验证令牌类型是否匹配
        if payload.get('is_refresh') != expect_refresh:
            logging.error(f"Token type mismatch: expected refresh={expect_refresh}")
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logging.error("Token has expired")
        return None
    except jwt.InvalidTokenError:
        logging.error("Invalid token")
        return None
    except Exception as e:
        logging.error(f"Token verification error: {e}")
        return None
