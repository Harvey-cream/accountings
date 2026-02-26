from django.urls import path
from .views import UserloginView, UserRegisterView

urlpatterns = [
    path('login/', UserloginView.as_view(), name='user_login'),
    path('register/', UserRegisterView.as_view(), name='user_register'),
]
