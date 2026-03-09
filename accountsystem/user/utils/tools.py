import base64
from io import BytesIO
import qrcode
import random
import string

def generate_account_id(user_model):
    """生成唯一的 8 位数字账号 ID"""
    while True:
        # 生成 8 位随机数字
        account_id = ''.join(random.choices(string.digits, k=8))
        # 确保不以 0 开头且在数据库中唯一
        if not account_id.startswith('0') and not user_model.objects.filter(account_id=account_id).exists():
            return account_id

def generate_qr_base64(data_str):
    """生成二维码并返回 Base64 字符串"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"
