
from django.db import models
from user.models import User

class TransactionIcon(models.Model):
    """图标库"""
    id = models.AutoField(primary_key=True, verbose_name="图标ID")
    name = models.CharField(max_length=50, verbose_name="图标名称", blank=True)
    icon = models.CharField(max_length=50, unique=True, verbose_name="图标值",blank=True) # 保证图标值唯一
    group = models.CharField(max_length=20, default='normal', verbose_name="图标分组") # normal 或 custom
    type = models.CharField(max_length=10, default='all', verbose_name="适用类型") # expense, income, all

    class Meta:
        verbose_name = "图标库"
        db_table = "transaction_icon"

class TransactionCategory(models.Model):
    """账单分类"""
    TYPE_CHOICES = (
        ('expense', '支出'),
        ('income', '收入'),
    )
    id = models.AutoField(primary_key=True, verbose_name="分类ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所属用户ID")
    name = models.CharField(max_length=20, verbose_name="分类名称")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='expense', verbose_name="账单类型")
    icon = models.ForeignKey(TransactionIcon, on_delete=models.CASCADE, verbose_name="关联图标ID")       
    sort = models.IntegerField(default=0, verbose_name="排序权重")

    class Meta:
        verbose_name = "账单分类"
        db_table = "transaction_category"

class TransactionRecord(models.Model):
    """账单记录"""
    TYPE_CHOICES = (
        ('expense', '支出'),
        ('income', '收入'),
    )
    id = models.AutoField(primary_key=True, verbose_name="记录ID")
    # 明确关联 User 的 id
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所属用户ID")
    category = models.ForeignKey(TransactionCategory, on_delete=models.CASCADE, verbose_name="所属分类ID")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="金额")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='expense', verbose_name="账单类型")
    date = models.DateField(verbose_name="消费日期")
    time = models.TimeField(verbose_name="消费时间")
    location = models.CharField(max_length=200, null=True, blank=True, verbose_name="地点")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "账单记录"
        db_table = "transaction_record"