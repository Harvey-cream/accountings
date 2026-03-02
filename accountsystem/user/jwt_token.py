import datetime
import logging
import os.path

import jwt

logger = logging.getLogger('django')

# 密钥，用于签名和验证JWT
SECRET_KEY = '0dfQ1jFw3zEusJs3m9xEIVsd_J8Lvf_p22Dml3GEoQ8'

Base_dir = os.path.dirname(os.path.abspath(__file__))
private_path = os.path.join(Base_dir,"private_key.pem")
public_path = os.path.join(Base_dir,"public_key.pem")

# 读取私钥
with open(private_path, "r") as f:
    PRIVATE_KEY = f.read()

# 读取公钥
with open(public_path, "r") as f:
    PUBLIC_KEY = f.read()

# 生成JWT
def generate_jwt(user_id, staff_user_id=None):
    """
    生成 JWT Token.
    
    Args:
        user_id: 登录的用户ID (企业登录时为企业账户ID)
        staff_user_id: 可选，员工个人账户ID (仅当企业员工登录时设置)
    """
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=365 * 24 * 60)
    payload = {
        'user_id': user_id,
        'exp': expiration_time.timestamp()
    }
    # 如果是员工登录企业账户，在 Token 中添加 staff_user_id
    if staff_user_id is not None:
        payload['staff_user_id'] = staff_user_id
    return jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')


# 验证JWT
def verify_jwt(token):
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


def decode_jwt_payload(token):
    """
    解码 JWT Token 并返回完整的 payload 字典。
    用于获取 staff_user_id 等额外信息。
    
    Returns:
        dict: 完整的 payload 字典，如果解码失败返回 None
    """
    if token is None:
        return None
    if token.startswith('Bearer '):
        token = token[7:]
    try:
        decoded_payload = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
        return decoded_payload
    except Exception as e:
        logger.error(f'token解码失败：{e}')
        return None



if __name__ == '__main__':
    # print("key:",secrets.token_urlsafe(32))
    user_token = generate_jwt(1)
    print("Generated Token:", user_token)
    print(verify_jwt(user_token))

    # from cryptography.hazmat.primitives import serialization
    # from cryptography.hazmat.primitives.asymmetric import rsa
    #
    # # 生成私钥
    # private_key = rsa.generate_private_key(
    #     public_exponent=65537,
    #     key_size=2048,
    # )
    #
    # # 将私钥保存到文件（PEM格式）
    # with open("private_key.pem", "wb") as f:
    #     f.write(private_key.private_bytes(
    #         encoding=serialization.Encoding.PEM,
    #         format=serialization.PrivateFormat.TraditionalOpenSSL,
    #         encryption_algorithm=serialization.NoEncryption(),
    #     ))
    #
    #     # 从私钥中提取公钥
    # public_key = private_key.public_key()
    #
    # # 将公钥保存到文件（PEM格式）
    # with open("public_key.pem", "wb") as f:
    #     f.write(public_key.public_bytes(
    #         encoding=serialization.Encoding.PEM,
    #         format=serialization.PublicFormat.SubjectPublicKeyInfo
    #     ))