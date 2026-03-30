import os
import sys
import django
from datetime import datetime

# 设置 Django 环境
# 获取 accountsystem 目录
accountsystem_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, accountsystem_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accountsystem.settings')
django.setup()

from account.models import AssetIcon, TransactionIcon
from system.models import SystemMessage

# ============ 图标数据定义 ============

# 1. 资产图标数据
ASSET_ICONS = [
    {'id': 1, 'name': '现金', 'icon': 'gold-coin', 'bg_class': 'icon-bg-green'},
    {'id': 2, 'name': '储蓄卡', 'icon': 'card', 'bg_class': 'icon-bg-yellow'},
    {'id': 3, 'name': '信用卡', 'icon': 'credit-pay', 'bg_class': 'icon-bg-orange'},
    {'id': 4, 'name': '虚拟账户', 'icon': 'gold-coin-o', 'bg_class': 'icon-bg-yellow-dark'},
    {'id': 5, 'name': '投资账户', 'icon': 'chart-trending-o', 'bg_class': 'icon-bg-orange-dark'},
    {'id': 6, 'name': '负债', 'icon': 'info', 'bg_class': 'icon-bg-red'},
    {'id': 7, 'name': '债权', 'icon': 'manager', 'bg_class': 'icon-bg-blue'},
    {'id': 8, 'name': '自定义资产', 'icon': 'points', 'bg_class': 'icon-bg-purple'}
]

# 2. 系统预设图标 (normal)
NORMAL_ICONS = [
    # 支出预设
    {'name': '餐饮', 'icon': 'logistics', 'type': 'expense'},
    {'name': '购物', 'icon': 'bag-o', 'type': 'expense'},
    {'name': '交通', 'icon': 'logistics', 'type': 'expense'},
    {'name': '娱乐', 'icon': 'video-o', 'type': 'expense'},
    {'name': '医疗', 'icon': 'friends-o', 'type': 'expense'},
    {'name': '学习', 'icon': 'bookmark-o', 'type': 'expense'},
    {'name': '房租', 'icon': 'wap-home-o', 'type': 'expense'},
    {'name': '其他', 'icon': 'ellipsis', 'type': 'expense'},
    
    # 更多支出
    {'name': '电影', 'icon': 'video-o', 'type': 'expense'},
    {'name': '运动', 'icon': 'fire-o', 'type': 'expense'},
    {'name': '礼物', 'icon': 'gift-o', 'type': 'expense'},
    {'name': '餐饮', 'icon': 'logistics', 'type': 'expense'},
    {'name': '办公', 'icon': 'description', 'type': 'expense'},
    {'name': '维修', 'icon': 'setting-o', 'type': 'expense'},
    {'name': '话费', 'icon': 'phone-o', 'type': 'expense'},
    {'name': '社交', 'icon': 'friends-o', 'type': 'expense'},
    {'name': '美发', 'icon': 'brush-o', 'type': 'expense'},
    {'name': '其他', 'icon': 'ellipsis', 'type': 'all'},

    # 收入预设
    {'name': '工资', 'icon': 'gold-coin-o', 'type': 'income'},
    {'name': '兼职', 'icon': 'records', 'type': 'income'},
    {'name': '理财', 'icon': 'balance-o', 'type': 'income'},
    {'name': '奖金', 'icon': 'diamond-o', 'type': 'income'},
    {'name': '报销', 'icon': 'notes-o', 'type': 'income'},
    {'name': '租金', 'icon': 'wap-home-o', 'type': 'income'},
    {'name': '分红', 'icon': 'chart-trending-o', 'type': 'income'},
    {'name': '其他', 'icon': 'ellipsis', 'type': 'all'},
    
    # 更多收入
    {'name': '礼金', 'icon': 'gift-o', 'type': 'income'},
    {'name': '退款', 'icon': 'refund-o', 'type': 'income'},
    {'name': '利息', 'icon': 'balance-list-o', 'type': 'income'},
    {'name': '二手', 'icon': 'shop-o', 'type': 'income'},
    {'name': '其他', 'icon': 'ellipsis', 'type': 'all'},
]

# 3. 自定义图标库 (custom)
CUSTOM_ICONS_CODES = [
    'shop-o', 'bag-o', 'brush-o', 'logistics', 'flower-o', 'cluster-o', 'cake', 'fire-o',
    'home-o', 'cart-o', 'phone-o', 'video-o', 'music-o', 'smile-o', 'gift-o', 'gem-o',
    'location-o', 'guide-o', 'hotel-o', 'flag-o', 'map-marked', 'photograph',
    'medal-o', 'points', 'underway-o', 'clock-o', 'bell', 'shield-o',
    'edit', 'notes-o', 'records', 'envelop-o', 'newspaper-o', 'award-o',
    'gold-coin-o', 'balance-o', 'card', 'bill-o', 'coupon-o', 'orders-o',
    'tv-o', 'bullhorn-o', 'photo-o', 'apps-o', 'filter-o', 'setting-o', 'user-o',
    'star-o', 'good-job-o', 'comment-o', 'manager-o', 'label-o', 'bookmark-o',
    'service-o', 'chat-o', 'search', 'ellipsis', 'exchange'
]

# 4. 系统消息数据
SYSTEM_MESSAGES = [
    {
        'id': 1,
        'title': '小龙记账',
        'content': '2025年账单来啦，',
        'link_text': '快来看看吧>>',
        'link_url': '/pages/chart/accounting_chart',
        'create_time': datetime.strptime('2026-03-07 16:34:23.587910', '%Y-%m-%d %H:%M:%S.%f')
    }
]

# ============ 初始化函数 ============

def init_asset_icons():
    """初始化资产图标"""
    print('开始导入资产图标数据...')
    
    count = 0
    for item in ASSET_ICONS:
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

    print(f'✓ 资产图标导入完成！共处理 {len(ASSET_ICONS)} 个，新增 {count} 个。')


def init_transaction_icons():
    """初始化交易图标"""
    print('开始导入交易图标数据...')
    
    # 1. 导入 NORMAL_ICONS (系统预设)
    normal_count = 0
    for item in NORMAL_ICONS:
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
                'name': '',
                'group': 'custom',
                'type': 'all'
            }
        )
        if created:
            custom_count += 1

    print(f'✓ 交易图标导入完成！')
    print(f'  - 预设图标: {normal_count} 个新增')
    print(f'  - 可选图标库: {custom_count} 个新增')


def init_system_messages():
    """初始化系统消息"""
    print('开始导入系统消息数据...')
    
    count = 0
    for data in SYSTEM_MESSAGES:
        msg, created = SystemMessage.objects.update_or_create(
            id=data['id'],
            defaults={
                'title': data['title'],
                'content': data['content'],
                'link_text': data['link_text'],
                'link_url': data['link_url'],
            }
        )
        
        # 强制更新时间字段
        SystemMessage.objects.filter(id=msg.id).update(create_time=data['create_time'])
        
        if created:
            count += 1

    print(f'✓ 系统消息导入完成！共处理 {len(SYSTEM_MESSAGES)} 条，新增 {count} 条。')


def init_all():
    """执行所有初始化"""
    print('=' * 50)
    print('开始执行数据初始化...')
    print('=' * 50)
    
    try:
        init_asset_icons()
        init_transaction_icons()
        init_system_messages()
        
        print('=' * 50)
        print('✓ 所有数据初始化完成！')
        print('=' * 50)
    except Exception as e:
        print(f'✗ 初始化失败: {str(e)}')
        raise


if __name__ == '__main__':
    init_all()
