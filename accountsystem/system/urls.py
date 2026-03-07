from django.urls import path
from .views import GetSystemMessageListView, MarkMessageReadView, GetUnreadMessageCountView

urlpatterns = [
    path('message/list/', GetSystemMessageListView.as_view(), name='get_system_messages'),
    path('message/read/', MarkMessageReadView.as_view(), name='mark_message_read'),
    path('message/unread/count/', GetUnreadMessageCountView.as_view(), name='get_unread_count'),
]
