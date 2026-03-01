import os
import sys
import django

# 设置 Django 环境
# 获取项目根目录 (accountsystem 所在目录)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accountsystem.settings')
django.setup()

from account.models import TransactionIcon
from account.utils.icons import NORMAL_ICONS, CUSTOM_ICONS_CODES

def move_icons():
    print('开始导入图标数据...')
    
    # 1. 导入 NORMAL_ICONS (系统预设)
    normal_count = 0
    for item in NORMAL_ICONS:
        # 使用 get_or_create 防止重复导入报错 (icon 是唯一的)
        obj, created = TransactionIcon.objects.get_or_create(
            icon=item['icon'],
            defaults={
                'name': item['name'],
                'group': 'normal',
                'type': item['type']
            }
        )
        if created:
            normal_count += 1
    
    # 2. 导入 CUSTOM_ICONS_CODES (可选图标库)
    custom_count = 0
    for icon_code in CUSTOM_ICONS_CODES:
        obj, created = TransactionIcon.objects.get_or_create(
            icon=icon_code,
            defaults={
                'name': '', # 自定义库通常没有固定名称
                'group': 'custom',
                'type': 'all'
            }
        )
        if created:
            custom_count += 1

    print(f'导入完成！')
    print(f'- 新增预设图标: {normal_count} 个')
    print(f'- 新增可选图标库: {custom_count} 个')

if __name__ == '__main__':
    move_icons()
