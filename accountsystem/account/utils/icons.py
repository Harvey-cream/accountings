# 1. 系统预设图标 (normal) - 对应 save_accouting.vue 中的各类预设
NORMAL_ICONS = [
    # 支出预设 (categories 数组)
    {'name': '餐饮', 'icon': 'logistics', 'type': 'expense'},
    {'name': '购物', 'icon': 'bag-o', 'type': 'expense'},
    {'name': '交通', 'icon': 'logistics', 'type': 'expense'},
    {'name': '娱乐', 'icon': 'video-o', 'type': 'expense'},
    {'name': '医疗', 'icon': 'friends-o', 'type': 'expense'},
    {'name': '学习', 'icon': 'bookmark-o', 'type': 'expense'},
    {'name': '房租', 'icon': 'wap-home-o', 'type': 'expense'},
    {'name': '其他', 'icon': 'ellipsis', 'type': 'expense'},
    
    # 更多支出 (moreIcons 数组)
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

    # 收入预设 (incomeCategories 数组)
    {'name': '工资', 'icon': 'gold-coin-o', 'type': 'income'},
    {'name': '兼职', 'icon': 'records', 'type': 'income'},
    {'name': '理财', 'icon': 'balance-o', 'type': 'income'},
    {'name': '奖金', 'icon': 'diamond-o', 'type': 'income'},
    {'name': '报销', 'icon': 'notes-o', 'type': 'income'},
    {'name': '租金', 'icon': 'wap-home-o', 'type': 'income'},
    {'name': '分红', 'icon': 'chart-trending-o', 'type': 'income'},
    {'name': '其他', 'icon': 'ellipsis', 'type': 'all'},
    
    # 更多收入 (moreIncomeIcons 数组)
    {'name': '礼金', 'icon': 'gift-o', 'type': 'income'},
    {'name': '退款', 'icon': 'refund-o', 'type': 'income'},
    {'name': '利息', 'icon': 'balance-list-o', 'type': 'income'},
    {'name': '二手', 'icon': 'shop-o', 'type': 'income'},
    {'name': '其他', 'icon': 'ellipsis', 'type': 'all'},
]

# 2. 自定义图标库 (custom) - 对应 category.vue 中的 availableIcons
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
