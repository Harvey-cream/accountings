import os
import django
import sys

# 将项目根目录添加到 python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accountsystem.settings')
django.setup()

from user.models import Medal

def seed_medals():
    medals_data = [
        # 坚持打卡
        {'id': 1, 'category': '坚持打卡', 'name': '初露锋芒', 'description': '连续打卡3天', 'icon': 'fire-o', 'requirement_type': 'checkin', 'requirement_value': 3, 'sort_order': 1},
        {'id': 2, 'category': '坚持打卡', 'name': '持之以恒', 'description': '连续打卡7天', 'icon': 'fire', 'requirement_type': 'checkin', 'requirement_value': 7, 'sort_order': 2},
        {'id': 3, 'category': '坚持打卡', 'name': '热力四射', 'description': '连续打卡15天', 'icon': 'hot-o', 'requirement_type': 'checkin', 'requirement_value': 15, 'sort_order': 3},
        {'id': 4, 'category': '坚持打卡', 'name': '习惯养成', 'description': '连续打卡30天', 'icon': 'hot', 'requirement_type': 'checkin', 'requirement_value': 30, 'sort_order': 4},
        {'id': 5, 'category': '坚持打卡', 'name': '打卡达人', 'description': '连续打卡100天', 'icon': 'gem-o', 'requirement_type': 'checkin', 'requirement_value': 100, 'sort_order': 5},
        {'id': 6, 'category': '坚持打卡', 'name': '钻石恒星', 'description': '连续打卡365天', 'icon': 'diamond', 'requirement_type': 'checkin', 'requirement_value': 365, 'sort_order': 6},
        
        # 记账成就
        {'id': 7, 'category': '记账成就', 'name': '记账新手', 'description': '累计记账10笔', 'icon': 'edit', 'requirement_type': 'bill', 'requirement_value': 10, 'sort_order': 7},
        {'id': 8, 'category': '记账成就', 'name': '记账能手', 'description': '累计记账100笔', 'icon': 'records', 'requirement_type': 'bill', 'requirement_value': 100, 'sort_order': 8},
        {'id': 9, 'category': '记账成就', 'name': '记账大师', 'description': '累计记账1000笔', 'icon': 'medal-o', 'requirement_type': 'bill', 'requirement_value': 1000, 'sort_order': 9},
        
        # 资产管理
        {'id': 10, 'category': '资产管理', 'name': '精打细算', 'description': '设置月度预算', 'icon': 'balance-list', 'requirement_type': 'budget', 'requirement_value': 1, 'sort_order': 10},
        {'id': 11, 'category': '资产管理', 'name': '财富管家', 'description': '添加3个资产账户', 'icon': 'gold-coin', 'requirement_type': 'asset', 'requirement_value': 3, 'sort_order': 11},
    ]

    for data in medals_data:
        Medal.objects.update_or_create(
            id=data['id'],
            defaults={
                'category': data['category'],
                'name': data['name'],
                'description': data['description'],
                'icon': data['icon'],
                'requirement_type': data['requirement_type'],
                'requirement_value': data['requirement_value'],
                'sort_order': data['sort_order']
            }
        )
    print("Medals seeded successfully!")

if __name__ == "__main__":
    seed_medals()
