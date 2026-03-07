from rest_framework.views import APIView
from common.response_web import HttpResult
from user.utils.user import get_current_user
from .models import SystemMessage, MessageReadState
from .serializers import SystemMessageSerializer
from django.db.models import Q

class GetSystemMessageListView(APIView):
    """获取系统消息列表"""
    def get(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
        
        # 获取针对该用户的消息，或者全局广播消息（user 为空）
        messages = SystemMessage.objects.filter(
            Q(user=user) | Q(user__isnull=True)
        ).order_by('-create_time')
        
        # 序列化并返回
        serializer = SystemMessageSerializer(messages, many=True, context={'request': request})
        return HttpResult.success_with_data("获取成功", serializer.data)

class GetUnreadMessageCountView(APIView):
    """获取未读消息数量"""
    def get(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
        
        # 1. 获取所有相关的消息（针对个人的或广播的）
        all_messages = SystemMessage.objects.filter(
            Q(user=user) | Q(user__isnull=True)
        )
        total_count = all_messages.count()
        
        # 2. 获取该用户已读的消息数量
        read_count = MessageReadState.objects.filter(user=user, message__in=all_messages).count()
        
        # 3. 计算未读数量
        unread_count = total_count - read_count
        
        return HttpResult.success_with_data("获取成功", {
            'unread_count': max(0, unread_count)
        })

class MarkMessageReadView(APIView):
    """标记消息为已读"""
    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
        
        message_id = request.data.get('id')
        if not message_id:
            return HttpResult.fail("消息ID不能为空")
            
        try:
            message = SystemMessage.objects.get(id=message_id)
            # 创建已读状态记录
            MessageReadState.objects.get_or_create(user=user, message=message)
            return HttpResult.success("标记已读成功")
        except SystemMessage.DoesNotExist:
            return HttpResult.fail("消息不存在")
        except Exception as e:
            return HttpResult.fail(f"操作失败: {str(e)}")
