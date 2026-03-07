import os
import django
import sys
from datetime import datetime

# 将项目根目录添加到 python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accountsystem.settings')
django.setup()

from system.models import SystemMessage

def seed_messages():
    # 数据定义
    messages_data = [
        {
            'id': 1,
            'title': '小龙记账',
            'content': '2025年账单来啦，',
            'link_text': '快来看看吧>>',
            'link_url': '/pages/chart/accounting_chart',
            'create_time': datetime.strptime('2026-03-07 16:34:23.587910', '%Y-%m-%d %H:%M:%S.%f')
        }
    ]

    for data in messages_data:
        # 使用 update_or_create 确保重复执行脚本不会产生多余数据
        msg, created = SystemMessage.objects.update_or_create(
            id=data['id'],
            defaults={
                'title': data['title'],
                'content': data['content'],
                'link_text': data['link_text'],
                'link_url': data['link_url'],
                # 注意：由于 models.py 中 create_time 带有 auto_now_add=True
                # 直接赋值可能被覆盖，如果需要强制指定时间，可以后续 save
            }
        )
        
        # 强制更新时间字段（针对 auto_now_add 字段的手动覆盖技巧）
        SystemMessage.objects.filter(id=msg.id).update(create_time=data['create_time'])
        
        status = "Created" if created else "Updated"
        print(f"[{status}] Message ID {msg.id}: {msg.content}")

    print("\nSystem messages seeded successfully!")

if __name__ == "__main__":
    seed_messages()
