from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from .models import UserPost, UserPostImage, UserComment, UserPostLike, UserFollow, UserNotice
from user.models import User, UserPointRecord
from user.utils.user_utils import get_current_user, upload_to_oss, sign_oss_url
from common.response_web import HttpResult
from .utils.comment_utils import format_time_ago
from django.db.models import Q

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
        
        # 这里的 images 是前端通过 uni.uploadFile 上传后拿到的 OSS URL 列表
        # 或者如果是原生表单上传，需要在这里处理 FILES
        images_urls = data.get('images', [])
        files = request.FILES.getlist('files') # 兼容多图上传

        if not content and not images_urls and not files:
            return HttpResult.fail("内容或图片不能为空")
        try:
            with transaction.atomic():
                # 1. 如果有实时上传的文件，先传到 OSS
                if files:
                    for f in files:
                        oss_url = upload_to_oss(f, folder='posts')
                        if oss_url:
                            images_urls.append(oss_url)

                # 2. 创建帖子记录
                post = UserPost.objects.create(
                    user=user,
                    content=content,
                    location=location,
                    is_public=is_public
                )
                
                # 3. 保存图片关联记录
                if images_urls:
                    image_objects = []
                    for index, img_url in enumerate(images_urls):
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
        post_type = data.get('type')
        user_id = data.get('userId')
        
        queryset = UserPost.objects.filter(is_public=True)
        
        if user_id:
            if user_id == 'self':
                if not user:
                    return HttpResult.fail("请先登录查看个人动态")
                queryset = queryset.filter(user=user)
            else:
                queryset = queryset.filter(user_id=user_id)
        
        if post_type is not None:
            post_type = int(post_type)
            if post_type == 1:
                queryset = queryset.order_by('-create_time')
            elif post_type == 0:
                queryset = queryset.order_by('-likes_count', '-create_time')
            elif post_type == 2:
                if not user:
                    return HttpResult.fail("请先登录查看关注动态")
                # 获取关注的人
                following_ids = UserFollow.objects.filter(user=user).values_list('followed_user_id', flat=True)
                queryset = queryset.filter(user_id__in=following_ids).order_by('-create_time')
        else:
            # 默认排序
            queryset = queryset.order_by('-create_time')
            
        posts_data = []
        for post in queryset[:20]:
            # 获取图片并生成签名 URL
            images = [sign_oss_url(img.image_url) for img in post.images.all().order_by('order')]
            
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
                        "avatar": sign_oss_url(child.user.avatar_url),
                        "content": child.content,
                        "reply_to": child.reply_to.nickname or child.reply_to.username if child.reply_to else None,
                        "time": format_time_ago(child.create_time),
                        "root_id": child.comment_root_id,
                    })

                real_comments.append({
                    "id": comment.id,
                    "author": comment.user.nickname or comment.user.username,
                    "authorId": comment.user.id,
                    "avatar": sign_oss_url(comment.user.avatar_url),
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
                "avatar": sign_oss_url(post.user.avatar_url),
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
                "authorId": user.id,
                "avatar": sign_oss_url(user.avatar_url),
                "content": comment.content,
                "time": "刚刚"
            })

        except UserPost.DoesNotExist:
            return HttpResult.fail("帖子不存在")
        except Exception as e:
            print(f"发布评论异常: {str(e)}")
            return HttpResult.fail(f"发布失败: {str(e)}")

class DeleteCommentView(APIView):
    """删除评论接口"""
    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
            
        comment_id = request.data.get('commentId')
        if not comment_id:
            return HttpResult.fail("参数错误")
            
        try:
            comment = UserComment.objects.get(id=comment_id)
            # 只能删除自己的评论
            if comment.user_id != user.id:
                return HttpResult.fail("无权删除他人的评论")
                
            comment.delete()
            return HttpResult.success("删除成功")
            
        except UserComment.DoesNotExist:
            return HttpResult.fail("评论不存在")
        except Exception as e:
            print(f"删除评论异常: {str(e)}")
            return HttpResult.fail(f"删除失败: {str(e)}")

class DeletePostView(APIView):
    """删除动态/帖子接口"""
    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
            
        post_id = request.data.get('postId')
        if not post_id:
            return HttpResult.fail("参数错误")
            
        try:
            post = UserPost.objects.get(id=post_id)
            # 只能删除自己的动态
            if post.user_id != user.id:
                return HttpResult.fail("无权删除他人的动态")
                
            post.delete()
            return HttpResult.success("动态已删除")
            
        except UserPost.DoesNotExist:
            return HttpResult.fail("动态不存在")
        except Exception as e:
            print(f"删除动态异常: {str(e)}")
            return HttpResult.fail(f"删除失败: {str(e)}")

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

class ToggleFollowView(APIView):
    """
    关注/取消关注接口
    """
    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
            
        data = request.data
        followed_user_id = data.get('followedUserId')
        is_follow = data.get('isFollow') # True: 关注, False: 取消

        if followed_user_id is None or is_follow is None:
            return HttpResult.fail("参数不完整")

        if int(followed_user_id) == user.id:
            return HttpResult.fail("不能关注自己")

        try:
            with transaction.atomic():
                followed_user = User.objects.get(id=followed_user_id)
                
                # 检查是否存在对称关注
                is_following_me = UserFollow.objects.filter(user=followed_user, followed_user=user).exists()
                
                if is_follow:
                    # 关注逻辑
                    follow, created = UserFollow.objects.get_or_create(
                        user=user, 
                        followed_user=followed_user
                    )
                    if created:
                        # 更新互关状态
                        if is_following_me:
                            follow.is_mutual = True
                            follow.save()
                            # 同时也把对方的互关状态改为 True
                            UserFollow.objects.filter(user=followed_user, followed_user=user).update(is_mutual=True)
                        
                        # 发送通知
                        UserNotice.objects.create(
                            user=followed_user,
                            sender=user,
                            notice_type='follow',
                            content="关注了你"
                        )
                else:
                    # 取消关注逻辑
                    UserFollow.objects.filter(user=user, followed_user=followed_user).delete()
                    # 如果之前是互关，取消对方的互关状态
                    if is_following_me:
                        UserFollow.objects.filter(user=followed_user, followed_user=user).update(is_mutual=False)

                # 获取最新的粉丝数返回给前端，保持同步
                followers_count = UserFollow.objects.filter(followed_user=followed_user).count()

                return HttpResult.success_with_data("操作成功", {
                    "followersCount": followers_count,
                    "isFollow": is_follow
                })
                
        except User.DoesNotExist:
            return HttpResult.fail("用户不存在")
        except Exception as e:
            print(f"关注操作异常: {str(e)}")
            return HttpResult.fail(f"操作失败: {str(e)}")

class UserFollowListView(APIView):
    """
    获取关注列表/粉丝列表
    """
    def get(self, request):
        user_id = request.query_params.get('userId')
        list_type = request.query_params.get('type') # 'following' or 'followers'

        if not user_id or not list_type:
            return HttpResult.fail("参数不完整")

        try:
            target_user = User.objects.get(id=user_id)
            if list_type == 'following':
                relations = UserFollow.objects.filter(user=target_user).select_related('followed_user')
                user_list = []
                for rel in relations:
                    user_list.append({
                        "userId": rel.followed_user.id,
                        "nickname": rel.followed_user.nickname or rel.followed_user.username,
                        "avatar": sign_oss_url(rel.followed_user.avatar_url),
                        "signature": rel.followed_user.signature,
                        "isMutual": rel.is_mutual
                    })
            else:
                relations = UserFollow.objects.filter(followed_user=target_user).select_related('user')
                user_list = []
                for rel in relations:
                    # 判断当前请求者是否也关注了这些粉丝
                    current_user = get_current_user(request)
                    is_following = False
                    if current_user:
                        is_following = UserFollow.objects.filter(user=current_user, followed_user=rel.user).exists()

                    user_list.append({
                        "userId": rel.user.id,
                        "nickname": rel.user.nickname or rel.user.username,
                        "avatar": sign_oss_url(rel.user.avatar_url),
                        "signature": rel.user.signature,
                        "isFollowing": is_following
                    })
            
            return HttpResult.success_with_data("获取成功", user_list)
        except User.DoesNotExist:
            return HttpResult.fail("用户不存在")
