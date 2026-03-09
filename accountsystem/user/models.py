from django.db import models
import uuid

class User(models.Model):
    username = models.CharField(max_length=50, null=True, blank=True, verbose_name="姓名")
    nickname = models.CharField(max_length=50, null=True, blank=True, verbose_name="昵称")
    account_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="账号ID")
    signature = models.CharField(max_length=200, null=True, blank=True, verbose_name="个性签名")
    gender = models.CharField(max_length=10, default="men", choices=(("men", "男"), ("women", "女")), verbose_name="性别")
    mobile = models.CharField(max_length=11, unique=True, null=True, verbose_name="手机号")
    password = models.CharField(max_length=128, verbose_name="密码")
    login_type = models.SmallIntegerField(default=1, verbose_name="登录类型")
    third_party_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="第三方唯一标识")
    refer_code = models.CharField(max_length=30, null=True, blank=True, verbose_name="推荐码")
    self_code = models.CharField(max_length=30, null=True, blank=True, verbose_name="自身邀请码")
    is_verified = models.BooleanField(default=False, verbose_name="是否认证")
    is_active = models.BooleanField(default=True, verbose_name="是否激活") # 添加此字段
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

class UserCheckIn(models.Model):
    """用户打卡记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    date = models.DateField(verbose_name="打卡日期")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "用户打卡"
        db_table = "user_check_in"
        unique_together = ('user', 'date')

class Medal(models.Model):
    """所有的勋章表"""
    REQUIREMENT_TYPE_CHOICES = (
        ('checkin', '打卡天数'),
        ('bill', '记账笔数'),
        ('budget', '预算设置'),
        ('asset', '资产账户'),
    )
    id = models.AutoField(primary_key=True, verbose_name="勋章ID")
    category = models.CharField(max_length=50, default="成就", verbose_name="分类名称")
    name = models.CharField(max_length=50, verbose_name="勋章名称")
    description = models.TextField(verbose_name="达成条件描述")
    icon = models.CharField(max_length=50, default="medal-o", verbose_name="图标名称")
    requirement_type = models.CharField(max_length=20, choices=REQUIREMENT_TYPE_CHOICES, default='checkin', verbose_name="解锁条件类型")
    requirement_value = models.IntegerField(default=1, verbose_name="解锁条件数值")
    sort_order = models.IntegerField(default=0, verbose_name="排序")

    class Meta:
        verbose_name = "勋章"
        verbose_name_plural = verbose_name
        db_table = "transaction_medal"
        ordering = ['sort_order']

    def __str__(self):
        return self.name

class UserMedal(models.Model):
    """用户解锁勋章的表"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    medal = models.ForeignKey(Medal, on_delete=models.CASCADE, verbose_name="勋章")
    unlock_time = models.DateTimeField(auto_now_add=True, verbose_name="解锁时间")

    class Meta:
        verbose_name = "用户已解锁勋章"
        verbose_name_plural = verbose_name
        db_table = "user_medal"
        unique_together = ('user', 'medal')

class UserPointRecord(models.Model):
    """用户积分流水表"""
    POINT_TYPE_CHOICES = (
        ('checkin', '每日签到'),
        ('task', '完成任务'),
        ('exchange', '积分兑换'),
        ('refund', '积分退还'),
        ('system', '系统赠送'),
    )
    
    DIRECTION_CHOICES = (
        ('income', '收入'),
        ('expense', '支出'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    amount = models.IntegerField(verbose_name="变动积分值") 
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='income', verbose_name="变动方向")
    type = models.CharField(max_length=20, choices=POINT_TYPE_CHOICES, verbose_name="业务类型")
    description = models.CharField(max_length=255, verbose_name="变动描述")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="记录时间")

    class Meta:
        verbose_name = "积分流水"
        verbose_name_plural = verbose_name
        db_table = "user_point_record"
        ordering = ['-create_time']

    def __str__(self):
        sign = '+' if self.direction == 'income' else '-'
        return f"{self.user.username}: {sign}{self.amount} ({self.type})"

