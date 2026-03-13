from django.db import models
from user.models import User

class UserPost(models.Model):
    """
    帖子模型 (主内容表)
    """
    content = models.TextField(verbose_name="帖子内容")
    likes_count = models.IntegerField(default=0, verbose_name="点赞数")
    view_count = models.IntegerField(default=0, verbose_name="浏览量")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name="发布者")
    is_public = models.BooleanField(default=True, verbose_name="是否公开")
    location = models.CharField(max_length=255, null=True, blank=True, verbose_name="发布位置")

    class Meta:
        verbose_name = "社区帖子"
        verbose_name_plural = verbose_name
        db_table = "user_community_post"
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.user.nickname or self.user.username} 的帖子: {self.content[:20]}"

class UserPostLike(models.Model):
    """
    点赞表
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes', verbose_name="点赞者")
    post = models.ForeignKey(UserPost, on_delete=models.CASCADE, related_name='post_likes', verbose_name="所属帖子")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="点赞时间")

    class Meta:
        verbose_name = "帖子点赞"
        verbose_name_plural = verbose_name
        db_table = "user_community_post_like"
        unique_together = ('user', 'post')

class UserPostImage(models.Model):
    """
    帖子图片表
    支持一个帖子对应多张图片
    """
    post = models.ForeignKey(UserPost, on_delete=models.CASCADE, related_name='images', verbose_name="所属帖子")
    image_url = models.TextField(verbose_name="图片地址")
    order = models.IntegerField(default=0, verbose_name="排序")

    class Meta:
        verbose_name = "帖子图片"
        verbose_name_plural = verbose_name
        db_table = "user_community_image"

class UserComment(models.Model):
    """
    精细化评论模型 (对齐抖音逻辑)
    1. 使用 SET_NULL 避免级联删除 (父删子存)
    2. 冗余存储被回复者 ID，即便父评论物理删除，子评论依然知道是在回复谁
    """
    post = models.ForeignKey(UserPost, on_delete=models.CASCADE, related_name='comments', verbose_name="所属帖子")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name="评论者")
    content = models.TextField(verbose_name="评论内容")
    # 1. 根评论 ID (root_id)：锁定所属的“评论树”
    # 父评论物理删除后，root 设为 null，子评论依然归属于该帖子，只是不再聚合显示    
    comment_root = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='root_replies', verbose_name="根评论ID")
    # 2. 父评论 ID (parent_id)：锁定准确的“回复对象 ID”
    # 父评论物理删除后，parent 设为 null，子评论变成本地一级评论，但 reply_to 还在
    comment_parent= models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_replies', verbose_name="父评论ID")
    # 3. 目标用户 ID (reply_to_id)：这是关键！
    # 即使父评论物理删除了，我们通过这个字段依然知道是在回复“谁”，前端显示不受影响
    reply_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_replies', verbose_name="被回复者ID")
    
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")
    likes_count = models.IntegerField(default=0, verbose_name="点赞数")

    class Meta:
        verbose_name = "社区评论"
        verbose_name_plural = verbose_name
        db_table = "user_community_comment"
        ordering = ['create_time']

    def __str__(self):
        user_name = self.user.nickname or self.user.username
        target_name = self.reply_to.nickname if self.reply_to else "帖子"
        return f"{user_name} 回复 {target_name}: {self.content[:20]}"
