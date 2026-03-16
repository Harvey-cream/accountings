from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from .models import UserPost, UserPostImage, UserComment, UserPostLike
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
            comments_queryset = post.comments.filter(comment_parent__isnull=True).order_by('-create_time')
            real_comments = []
            for comment in comments_queryset:
                # 获取该根评论下的子评论 (前2条)
                child_comments_queryset = post.comments.filter(comment_root=comment).order_by('create_time')
                child_comments = []
                for child in child_comments_queryset[:2]:
                    child_comments.append({
                        "id": child.id,
                        "author": child.user.nickname or child.user.username,
                        "authorId": child.user.id,
                        "avatar": child.user.avatar_url,
                        "content": child.content,
                        "reply_to": child.reply_to.nickname or child.reply_to.username if child.reply_to else None,
                        "time": format_time_ago(child.create_time),
                        "root_id": child.comment_root_id,
                    })

                real_comments.append({
                    "id": comment.id,
                    "author": comment.user.nickname or comment.user.username,
                    "authorId": comment.user.id,
                    "avatar": comment.user.avatar_url,
                    "content": comment.content,
                    "likes": comment.likes_count,
                    "time": format_time_ago(comment.create_time),
                    "root_id": comment.comment_root_id,
                    "child_comments": child_comments,
                    "child_count": child_comments_queryset.count()
                })

            # 检查当前用户是否点赞
            is_liked = False
            if user:
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

class PublishCommentView(APIView):
    """发表评论"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
        
        data = request.data
        post_id = data.get('post_id')
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id') # 上一级评论 ID
        root_id = data.get('root_id')     # 根评论 ID
        reply_to_id = data.get('reply_to_id') # 被回复者 ID

        if not post_id or not content:
            return HttpResult.fail("帖子ID或内容不能为空")

        try:
            post = UserPost.objects.get(id=post_id)
            
            # 处理根评论和父评论
            comment_parent = None
            comment_root = None
            reply_to = None

            if parent_id:
                try:
                    comment_parent = UserComment.objects.get(id=parent_id)
                    # 默认回复父评论的作者
                    reply_to = comment_parent.user
                    
                    # 根评论逻辑：
                    # 如果父评论本身没有 root，说明父评论就是 root
                    # 否则，当前评论的 root 应该和父评论的 root 一致
                    comment_root = comment_parent.comment_root or comment_parent
                    
                    # 如果前端显式传了 root_id，则以前端为准 (多级回复场景)
                    if root_id:
                        try:
                            comment_root = UserComment.objects.get(id=root_id)
                        except UserComment.DoesNotExist:
                            pass
                    
                    # 如果前端显式传了 reply_to_id，则以前端为准
                    if reply_to_id:
                        try:
                            reply_to = User.objects.get(id=reply_to_id)
                        except User.DoesNotExist:
                            pass
                except UserComment.DoesNotExist:
                    return HttpResult.fail("回复的评论不存在")

            comment = UserComment.objects.create(
                post=post,
                user=user,
                content=content,
                comment_parent=comment_parent,
                comment_root=comment_root,
                reply_to=reply_to
            )

            return HttpResult.success_with_data("评论成功", {
                "id": comment.id,
                "author": user.nickname or user.username,
                "avatar": user.avatar_url,
                "content": comment.content,
                "time": "刚刚"
            })

        except UserPost.DoesNotExist:
            return HttpResult.fail("帖子不存在")
        except Exception as e:
            print(f"发表评论异常: {str(e)}")
            return HttpResult.fail(f"评论失败: {str(e)}")

class LikePostView(APIView):
    """
    点赞/取消点赞接口
    GET: 获取当前点赞状态和点赞总数
    POST: 切换点赞状态 (接收前端防抖后的最终状态)
    """
    def get(self, request):
        user = get_current_user(request)
        post_id = request.query_params.get('postId')
        if not post_id:
            return HttpResult.fail("帖子ID不能为空")
            
        try:
            post = UserPost.objects.get(id=post_id)
            is_liked = False
            if user:
                is_liked = UserPostLike.objects.filter(user=user, post=post).exists()
            
            return HttpResult.success_with_data("获取成功", {
                "isLiked": is_liked,
                "likesCount": post.likes_count
            })
        except UserPost.DoesNotExist:
            return HttpResult.fail("帖子不存在")

    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
            
        data = request.data
        post_id = data.get('postId')
        # 前端同步过来的最终状态 (True: 点赞, False: 取消)
        is_liked_state = data.get('isLiked') 

        if post_id is None or is_liked_state is None:
            return HttpResult.fail("参数不完整")

        try:
            with transaction.atomic():
                # 使用 select_for_update 锁定帖子记录，防止并发更新 likes_count 出错
                post = UserPost.objects.select_for_update().get(id=post_id)
                
                # 检查数据库中当前的实际状态
                like_exists = UserPostLike.objects.filter(user=user, post=post).exists()
                
                if is_liked_state:
                    # 如果前端传的是“点赞”状态
                    if not like_exists:
                        # 只有数据库没记录时才创建，并增加计数
                        UserPostLike.objects.create(user=user, post=post)
                        post.likes_count += 1
                        post.save()
                else:
                    # 如果前端传的是“取消点赞”状态
                    if like_exists:
                        # 只有数据库有记录时才删除，并减少计数
                        UserPostLike.objects.filter(user=user, post=post).delete()
                        post.likes_count = max(0, post.likes_count - 1)
                        post.save()
                
                return HttpResult.success_with_data("同步成功", {
                    "isLiked": is_liked_state,
                    "likesCount": post.likes_count
                })
                
        except UserPost.DoesNotExist:
            return HttpResult.fail("帖子不存在")
        except Exception as e:
            print(f"点赞同步异常: {str(e)}")
            return HttpResult.fail(f"点赞同步失败: {str(e)}")
