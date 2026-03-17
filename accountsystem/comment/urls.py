from django.urls import path
from .views import (
    PublishPostView, PostListView, PublishCommentView, LikePostView,
    ToggleFollowView, UserFollowListView
)

urlpatterns = [
    path('post/publish/', PublishPostView.as_view(), name='publish_post'),
    path('post/list/', PostListView.as_view(), name='post_list'),
    path('post/like/', LikePostView.as_view(), name='like_post'),
    path('publish/', PublishCommentView.as_view(), name='publish_comment'),
    path('follow/toggle/', ToggleFollowView.as_view(), name='toggle_follow'),
    path('follow/list/', UserFollowListView.as_view(), name='follow_list'),
]
