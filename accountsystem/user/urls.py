from django.urls import path
from .views import ( UserloginView, UserRegisterView, RefreshTokenView, GetUserInfoView, UserCheckInView, GetUserStatsView, GetMedalListView, GetUserPointsView, UserPointSignInView, GetInviteQRView, UpdateUserInfoView
)

urlpatterns = [
    path('login/', UserloginView.as_view(), name='user_login'),
    path('register/', UserRegisterView.as_view(), name='user_register'),
    path('refresh_token/', RefreshTokenView.as_view(), name='refresh_token'),
    path('info/', GetUserInfoView.as_view(), name='user_info'),
    path('info/update/', UpdateUserInfoView.as_view(), name='update_user_info'),
    path('checkin/', UserCheckInView.as_view(), name='user_checkin'),
    path('stats/', GetUserStatsView.as_view(), name='get_user_stats'),
    path('medal/list/', GetMedalListView.as_view(), name='get_medal_list'),
    path('points/', GetUserPointsView.as_view(), name='get_user_points'),
    path('points/signin/', UserPointSignInView.as_view(), name='user_point_signin'),
    path('invite/qr/', GetInviteQRView.as_view(), name='get_invite_qr'),
]
