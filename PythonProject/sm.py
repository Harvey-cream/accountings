# generate_sm2_key.py（适配所有gmssl版本）
from gmssl import sm2

# 步骤1：先初始化一个临时实例（传空占位符，满足参数要求）
temp_sm2 = sm2.CryptSM2(public_key=None, private_key=None, mode=1)

# 步骤2：生成私钥（64字符，后端解密用）
private_key = temp_sm2.generate_private_key()

# 步骤3：生成对应公钥（先生成不带04前缀的，再补04）
public_key_without_04 = temp_sm2.generate_public_key(private_key)
public_key = "04" + public_key_without_04  # 补04前缀，适配前端

# 步骤4：打印结果（复制这些值到前后端）
print("===== 生成的SM2密钥对（复制到对应位置） =====")
print("🔑 后端私钥（替换BACK_PRIVATE_KEY）：")
print(private_key)
print("\n🔑 前端/后端公钥（替换BACK_PUBLIC_KEY/前端BACK_PUBLIC_KEY）：")
print(public_key)

# 验证：用生成的密钥对测试加解密（确保可用）
test_sm2 = sm2.CryptSM2(public_key=public_key_without_04, private_key=private_key, mode=1)
test_str = "123456"
# 加密
enc_bytes = test_sm2.encrypt(test_str.encode("utf-8"))
enc_hex = enc_bytes.hex()
# 解密
dec_bytes = test_sm2.decrypt(enc_bytes)
dec_str = dec_bytes.decode("utf-8")

print("\n===== 加解密验证 =====")
print(f"测试明文：{test_str}")
print(f"加密后Hex：{enc_hex[:50]}...")  # 只打印前50位
print(f"解密后明文：{dec_str}")
print(f"✅ 密钥对是否有效：{dec_str == test_str}")