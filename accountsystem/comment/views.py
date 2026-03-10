from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from .models import UserPost, UserPostImage
from user.models import User, UserPointRecord
from user.utils.user_utils import get_current_user
from common.response_web import HttpResult
from .utils.comment_utils import format_time_ago

class PublishPostView(APIView):
    """发布动态/帖子"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
        
        data = request.data
        content = data.get('content', '').strip()
        location = data.get('location', '')
        is_public = data.get('is_hidden', True) # 前端传的是 is_hidden，对应逻辑：True为公开
        images = data.get('images', [])

        # 1. 参数校验
        if not content and not images:
            return HttpResult.fail("内容或图片不能为空")

        # 2. 业务逻辑处理
        try:
            with transaction.atomic():
                # 创建帖子记录
                post = UserPost.objects.create(
                    user=user,
                    content=content,
                    location=location,
                    is_public=is_public
                )
                # 保存图片
                if images and isinstance(images, list):
                    image_objects = []
                    for index, img_url in enumerate(images):
                        image_objects.append(UserPostImage(
                            post=post,
                            image_url=img_url,
                            order=index
                        ))
                    if image_objects:
                        UserPostImage.objects.bulk_create(image_objects)

                return HttpResult.success_with_data("发布成功", {
                    "id": post.id
                })

        except Exception as e:
            print(f"发布动态异常: {str(e)}")
            return HttpResult.fail(f"发布失败: {str(e)}")

class PostListView(APIView):
    """获取动态列表"""
    def get(self, request, format=None):
        user = get_current_user(request)
        
        data = request.query_params
        post_type = int(data.get('type', 0)) # 0: 热门推荐, 1: 最新发布, 2: 我的关注
        
        queryset = UserPost.objects.filter(is_public=True)
        
        if post_type == 1:
            queryset = queryset.order_by('-create_time')
        elif post_type == 0:
            queryset = queryset.order_by('-likes_count', '-create_time')
        elif post_type == 2:
            if not user:
                return HttpResult.fail("请先登录查看关注动态")
            queryset = queryset.order_by('-create_time')
            
        posts_data = []
        for post in queryset[:20]:
            # 获取图片
            images = [img.image_url for img in post.images.all().order_by('order')]
            
            # 获取前2条评论
            comments_queryset = post.comments.filter(parent__isnull=True).order_by('-create_time')
            real_comments = []
            for comment in comments_queryset:
                real_comments.append({
                    "id": comment.id,
                    "author": comment.user.nickname or comment.user.username,
                    "authorId": comment.user.id,
                    "avatar": comment.user.avatar_url,
                    "content": comment.content,
                    "time": format_time_ago(comment.create_time),
                })

            # 检查当前用户是否点赞
            is_liked = False
            if user:
                from .models import UserPostLike
                is_liked = UserPostLike.objects.filter(user=user, post=post).exists()

            posts_data.append({
                "postId": post.id,
                "userId": post.user.id,
                "name": post.user.nickname or post.user.username,
                "avatar": post.user.avatar_url,
                "time": format_time_ago(post.create_time),
                "text": post.content,
                "hasImages": len(images) > 0,
                "images": images,
                "likes": post.likes_count,
                "isLiked": is_liked,
                "comments": post.comments.count(),
                "realComments": real_comments,
                "location": post.location,
                "showAllComments": False
            })
            
        return HttpResult.success_with_data("获取成功", posts_data)
