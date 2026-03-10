from django.utils import timezone

def format_time_ago(dt):
    """
    格式化时间为“多久以前”
    """
    if not dt:
        return ""
        
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 0:
        if diff.days < 7:
            return f"{diff.days}天前"
        return dt.strftime('%Y-%m-%d')
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}小时前"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}分钟前"
    else:
        return "刚刚"
