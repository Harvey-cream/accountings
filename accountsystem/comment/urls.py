from django.urls import path
from .views import PublishPostView, PostListView

urlpatterns = [
    path('post/publish/', PublishPostView.as_view(), name='publish_post'),
    path('post/list/', PostListView.as_view(), name='post_list'),
]
