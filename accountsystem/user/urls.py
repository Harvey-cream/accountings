from django.urls import path
from .views import UserloginView, UserRegisterView, RefreshTokenView, GetUserInfoView

urlpatterns = [
    path('login/', UserloginView.as_view(), name='user_login'),
    path('register/', UserRegisterView.as_view(), name='user_register'),
    path('refresh_token/', RefreshTokenView.as_view(), name='refresh_token'),
    path('info/', GetUserInfoView.as_view(), name='user_info'),
]
