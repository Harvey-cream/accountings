from django.urls import path
from .views import GetIconsView, SaveBillView

urlpatterns = [
    path('icons/', GetIconsView.as_view(), name='get_icons'),
    path('bill/save/', SaveBillView.as_view(), name='save_bill'),
]
