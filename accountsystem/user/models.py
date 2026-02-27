from django.db import models
import uuid

class User(models.Model):
    username = models.CharField(max_length=50, null=True, blank=True, verbose_name="姓名")
    mobile = models.CharField(max_length=11, unique=True, null=True, verbose_name="手机号")
    password = models.CharField(max_length=128, verbose_name="密码")
    login_type = models.SmallIntegerField(default=1, verbose_name="登录类型")
    third_party_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="第三方唯一标识")
    refer_code = models.CharField(max_length=30, null=True, blank=True, verbose_name="推荐码")
    self_code = models.CharField(max_length=30, null=True, blank=True, verbose_name="自身邀请码")
    is_verified = models.BooleanField(default=False, verbose_name="是否认证")
    role_id = models.IntegerField(null=True, blank=True, verbose_name="VIP角色ID")
    avatar_url = models.TextField(null=True, blank=True, verbose_name="用户头像地址")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="注册时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    last_login_time = models.DateTimeField(null=True, blank=True, verbose_name="上次登录时间")

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name
        db_table = "user"

    def __str__(self):
        return self.username or self.mobile or str(self.id)

