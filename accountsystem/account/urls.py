from django.urls import path
from .views import GetIconsView

urlpatterns = [
    path('icons/', GetIconsView.as_view(), name='get_icons'),
]
