from rest_framework import serializers
from .models import SystemMessage, MessageReadState
from user.utils.user import get_current_user

class SystemMessageSerializer(serializers.ModelSerializer):
    # 自定义字段，用于返回格式化后的时间
    time = serializers.SerializerMethodField()
    # 是否已读字段
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = SystemMessage
        fields = ['id', 'title', 'content', 'link_text', 'link_url', 'time', 'is_read']

    def get_time(self, obj):
        # 格式化为 01-03 14:18 这种格式，匹配前端需求
        return obj.create_time.strftime('%m-%d %H:%M')

    def get_is_read(self, obj):
        # 兼容手动获取当前用户的方式
        request = self.context.get('request')
        user = get_current_user(request)
        if user:
            return MessageReadState.objects.filter(user=user, message=obj).exists()
        return False
