from gmssl import sm2, sm3, func
import base64
import random
import string
from binascii import unhexlify, hexlify

# --- 密钥配置 ---
# PAIR 1: 前端请求后端 (前端用公钥加密，后端用私钥解密)
BACK_PRIVATE_KEY = "8547188426b95afd9a152685d9eb73d224d09cba131026bf61df7c2c9d473c62"
BACK_PUBLIC_KEY = "040f7b69db681310cf0c56ea8f853eaf2164b274bcfb178850547d45235861ecc729378da575b33d3badd2060a26593cfca227be3a3c837e106cb1a4aac32a823b"

# PAIR 2: 后端响应前端 (后端用私钥加密，前端用公钥解密)
FRONT_PUBLIC_KEY = "04475516a0b2e6fddb0eede456ebef869c06db3d70658717d3f00fe8ac387b291dbe24d97d1b7dec12a340e1ea43bac0d17f0480732287aafbf623c00bd8d6de84"
FRONT_PRIVATE_KEY = "a543b37a621e06ef3ce89eca78a79f2296c0415d009df2ff3ceb688cdf1fa8e8"

# 获取sm2对象 
def get_sm2(pub_key, pri_key): 
    # 去掉 04 前缀进行初始化是 gmssl 的标准做法
    if pub_key and pub_key.startswith("04"):
        pub_key = pub_key[2:]
    return sm2.CryptSM2(public_key=pub_key, private_key=pri_key, mode=1)

class SM2Utils:
    def __init__(self, public_key=None, private_key=None):
        self.public_key = public_key
        self.private_key = private_key
        self.sm2_crypt = get_sm2(public_key, private_key)

    def encrypt(self, data):
        if not self.public_key:
            raise ValueError("公钥未设置")
        enc_data = self.sm2_crypt.encrypt(data.encode('utf-8'))
        return hexlify(enc_data).decode('utf-8')

    def decrypt(self, data):
        if not self.private_key:
            raise ValueError("私钥未设置")
        
        print(f"--- SM2 解密调试 ---")
        print(f"收到密文 (Hex): {data}")
        
        try:
            # 核心：使用 unhexlify 将十六进制字符串转换为字节流并解密
            raw_bytes = unhexlify(data)
            dec_bytes = self.sm2_crypt.decrypt(raw_bytes)
            print(f"解密出原始字节: {dec_bytes}")
            
            result = dec_bytes.decode("utf-8")
            print(f"解密出明文成功: {result}")
            return result
        except Exception as e:
            print(f"解密异常报错: {e}")
            raise e

def sm3_hash(data):
    return sm3.sm3_hash(func.bytes_to_list(data.encode('utf-8')))

def get_refer_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# 初始化工具实例
# 修复：必须传入对应的公钥，算法才能正常工作
request_handler = SM2Utils(public_key=BACK_PUBLIC_KEY, private_key=BACK_PRIVATE_KEY)
response_handler = SM2Utils(public_key=FRONT_PUBLIC_KEY, private_key=FRONT_PRIVATE_KEY)
