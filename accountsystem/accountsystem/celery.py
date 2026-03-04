import os
from celery import Celery

# 设置 Django 默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accountsystem.settings')

app = Celery('accountsystem')

# 使用字符串以确保 worker 不必序列化对象
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从所有已注册的 app 中加载任务
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
