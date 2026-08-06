
from django.db import models
from user.models import User

class TransactionIcon(models.Model):
    """图标库"""
    id = models.AutoField(primary_key=True, verbose_name="图标ID")
    name = models.CharField(max_length=50, verbose_name="图标名称", blank=True)
    icon = models.CharField(max_length=50, unique=True, verbose_name="图标值", blank=True) # 保证图标值唯一
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
    count = models.IntegerField(default=0, verbose_name="账单数量") # 统计该用户该分类下的账单笔数
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="最后更新时间") # 每次该分类下产生新账单时更新

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

class TransactionBudget(models.Model):
    """预算管理"""
    BUDGET_TYPE_CHOICES = (
        ('month', '月预算'),
        ('year', '年预算'),
    )
    id = models.AutoField(primary_key=True, verbose_name="预算ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所属用户ID")
    is_total = models.BooleanField(default=False, verbose_name="是否为总预算") # True 表示总预算，False 表示分类预算
    category = models.ForeignKey(TransactionCategory, on_delete=models.CASCADE, null=True, blank=True, verbose_name="关联分类ID") 
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="预算金额")
    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPE_CHOICES, default='month', verbose_name="预算类型")
    period = models.CharField(max_length=20, verbose_name="预算周期") # 存储格式如 "2023-02" 或 "2023"
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "预算管理"
        db_table = "transaction_budget"
        # 确保同一个用户在同一个周期内，针对同一个分类（或总预算）只有一个预算记录
        unique_together = ('user', 'category', 'budget_type', 'period', 'is_total')

class AssetIcon(models.Model):
    """资产图标库"""
    id = models.AutoField(primary_key=True, verbose_name="图标ID")
    name = models.CharField(max_length=20, verbose_name="图标名称")
    icon = models.CharField(max_length=50, verbose_name="图标代码") # 对应 vant icon 名称
    bg_class = models.CharField(max_length=50, verbose_name="背景类名") # 对应前端的 bg-green 等
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "资产图标"
        db_table = "transaction_asset_icon"

class AssetAccount(models.Model):
    """资产账户表"""
    ACCOUNT_TYPE_CHOICES = (
        ('asset', '资产'),
        ('debt', '负债'),
    )
    id = models.AutoField(primary_key=True, verbose_name="账户ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所属用户ID")
    name = models.CharField(max_length=50, verbose_name="账户名称") # 如：招商银行、我的钱包
    asset_type = models.ForeignKey(AssetIcon, on_delete=models.PROTECT, verbose_name="资产类型图标")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="账户余额")
    type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='asset', verbose_name="账户类型")
    is_included_in_total = models.BooleanField(default=True, verbose_name="是否计入总资产")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "资产账户"
        db_table = "transaction_asset"

class TransactionInvoice(models.Model):
    """发票信息表"""
    id = models.AutoField(primary_key=True, verbose_name="发票ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所属用户ID")
    name = models.CharField(max_length=100, verbose_name="抬头名称")
    tax_id = models.CharField(max_length=50, verbose_name="税号") 
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name="单位地址")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="电话号码")
    bank = models.CharField(max_length=100, null=True, blank=True, verbose_name="开户银行")
    account = models.CharField(max_length=50, null=True, blank=True, verbose_name="银行账号")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="发票金额")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "发票助手"
        db_table = "transaction_invoice"

class LangchainChatMessage(models.Model):
    """AI 记账对话记录"""
    ROLE_CHOICES = (
        ('user', '用户'),
        ('ai', 'AI'),
    )
    MSG_TYPE_CHOICES = (
        ('text', '纯文本'),
        ('text_image', '图文'),
        ('transaction', '账单卡片'),
        ('confirm', '确认卡片'),
    )
    id = models.AutoField(primary_key=True, verbose_name="消息ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所属用户ID")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="角色")
    type = models.CharField(max_length=20, choices=MSG_TYPE_CHOICES, default='text', verbose_name="消息类型")
    content = models.TextField(verbose_name="文本内容", blank=True, null=True)
    image_url = models.CharField(max_length=500, verbose_name="图片地址", blank=True, null=True)
    extra_data = models.TextField(verbose_name="额外结构化数据(JSON)", null=True, blank=True)
    record = models.ForeignKey(TransactionRecord, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联账单记录")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")

    class Meta:
        verbose_name = "AI 对话记录"
        db_table = "transaction_langchain_chat"
        ordering = ['create_time']

