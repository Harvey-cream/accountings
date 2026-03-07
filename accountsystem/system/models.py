from django.db import models
from user.models import User

class SystemMessage(models.Model):
    """系统消息内容"""
    id = models.AutoField(primary_key=True, verbose_name="消息ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="接收用户") # 为空表示广播消息
    title = models.CharField(max_length=100, default="小龙记账", verbose_name="发送者名称")
    content = models.TextField(verbose_name="消息内容")
    link_text = models.CharField(max_length=100, null=True, blank=True, verbose_name="链接文本")
    link_url = models.CharField(max_length=255, null=True, blank=True, verbose_name="跳转链接")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")

    class Meta:
        verbose_name = "系统消息"
        verbose_name_plural = verbose_name
        db_table = "system_message"
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.title}: {self.content[:20]}..."

class MessageReadState(models.Model):
    """用户对消息的阅读状态"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    message = models.ForeignKey(SystemMessage, on_delete=models.CASCADE, verbose_name="消息")
    read_time = models.DateTimeField(auto_now_add=True, verbose_name="阅读时间")

    class Meta:
        verbose_name = "消息已读状态"
        db_table = "system_message_read"
        unique_together = ('user', 'message') 
