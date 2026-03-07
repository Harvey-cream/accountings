from rest_framework import serializers
from .models import Medal, UserMedal
from .utils.user_utils import get_current_user

class MedalSerializer(serializers.ModelSerializer):
    """勋章序列化器"""
    unlocked = serializers.SerializerMethodField()
    unlock_time = serializers.SerializerMethodField()

    class Meta:
        model = Medal
        fields = ['id', 'category', 'name', 'description', 'icon', 'sort_order', 'unlocked', 'unlock_time']

    def get_unlocked(self, obj):
        user = get_current_user(self.context.get('request'))
        if user:
            return UserMedal.objects.filter(user=user, medal=obj).exists()
        return False

    def get_unlock_time(self, obj):
        user = get_current_user(self.context.get('request'))
        if user:
            user_medal = UserMedal.objects.filter(user=user, medal=obj).first()
            if user_medal:
                return user_medal.unlock_time.strftime('%Y-%m-%d %H:%M')
        return None
