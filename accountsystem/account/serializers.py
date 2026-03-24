from rest_framework import serializers
import json
from .models import LangchainChatMessage

class LangchainChatMessageSerializer(serializers.ModelSerializer):
    """AI 记账对话记录序列化器"""
    # 使用 JSONField 自动处理 TextField 中的 JSON 字符串与 Python 对象之间的转换
    extra_data = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = LangchainChatMessage
        fields = ['id', 'user', 'role', 'type', 'content', 'image_url', 'extra_data', 'record', 'create_time']
        read_only_fields = ['id', 'create_time']

    def to_representation(self, instance):
        """在返回数据给前端时，确保 extra_data 是解析后的 JSON 对象而非字符串"""
        # 如果关联的账单记录已被删除，则该卡片消息不应显示（返回 None，由视图过滤）
        if instance.type == 'transaction' and instance.record_id and not instance.record:
            return None
            
        ret = super().to_representation(instance)
        if isinstance(ret.get('extra_data'), str):
            try:
                ret['extra_data'] = json.loads(ret['extra_data'])
            except (ValueError, TypeError):
                pass
        return ret

    def to_internal_value(self, data):
        """在保存前端数据到数据库前，将 extra_data 转为字符串存储"""
        # 如果前端传的是对象，DRF 的 JSONField 会处理。
        # 这里我们确保它最终能存入 TextField
        ret = super().to_internal_value(data)
        if 'extra_data' in ret and not isinstance(ret['extra_data'], str):
            ret['extra_data'] = json.dumps(ret['extra_data'], ensure_ascii=False)
        return ret
