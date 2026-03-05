import os
import sys
import django

# 设置 Django 环境
# 获取项目根目录 (accountsystem 所在目录)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accountsystem.settings')
django.setup()

from account.models import AssetIcon

def init_asset_icons():
    print('开始导入资产图标数据...')
    
    asset_icons = [
        {'id': 1, 'name': '现金', 'icon': 'gold-coin', 'bg_class': 'icon-bg-green'},
        {'id': 2, 'name': '储蓄卡', 'icon': 'card', 'bg_class': 'icon-bg-yellow'},
        {'id': 3, 'name': '信用卡', 'icon': 'credit-pay', 'bg_class': 'icon-bg-orange'},
        {'id': 4, 'name': '虚拟账户', 'icon': 'gold-coin-o', 'bg_class': 'icon-bg-yellow-dark'},
        {'id': 5, 'name': '投资账户', 'icon': 'chart-trending-o', 'bg_class': 'icon-bg-orange-dark'},
        {'id': 6, 'name': '负债', 'icon': 'info', 'bg_class': 'icon-bg-red'},
        {'id': 7, 'name': '债权', 'icon': 'manager', 'bg_class': 'icon-bg-blue'},
        {'id': 8, 'name': '自定义资产', 'icon': 'points', 'bg_class': 'icon-bg-purple'}
    ]

    count = 0
    for item in asset_icons:
        obj, created = AssetIcon.objects.get_or_create(
            id=item['id'],
            defaults={
                'name': item['name'],
                'icon': item['icon'],
                'bg_class': item['bg_class']
            }
        )
        if created:
            count += 1
        else:
            # 如果已存在则更新，确保数据同步
            obj.name = item['name']
            obj.icon = item['icon']
            obj.bg_class = item['bg_class']
            obj.save()

    print(f'导入完成！共处理 {len(asset_icons)} 个资产图标，其中新新增 {count} 个。')

if __name__ == '__main__':
    init_asset_icons()
