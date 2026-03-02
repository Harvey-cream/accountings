from datetime import datetime
from django.utils import timezone

def format_datetime(dt):
    """
    将 datetime 对象格式化为 'YYYY-MM-DD HH:MM:SS' 字符串
    """
    if not dt:
        return ""
    if isinstance(dt, str):
        return dt
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_date(d):
    """
    将 date 对象格式化为 'YYYY-MM-DD' 字符串
    """
    if not d:
        return ""
    if isinstance(d, str):
        return d
    return d.strftime('%Y-%m-%d')

def parse_date(date_str):
    """
    解析日期字符串，支持 M/D/YYYY 和 YYYY-MM-DD 格式
    """
    if not date_str:
        return timezone.now().date()
    try:
        if '/' in date_str:
            # 处理 M/D/YYYY
            return datetime.strptime(date_str, '%m/%d/%Y').date()
        else:
            # 处理 YYYY-MM-DD
            return datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return timezone.now().date()
