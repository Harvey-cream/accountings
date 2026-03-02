from django.urls import path
from .views import GetIconsView, SaveBillView, GetBillListView, DeleteBillView

urlpatterns = [
    path('icons/', GetIconsView.as_view(), name='get_icons'),
    path('bill/save/', SaveBillView.as_view(), name='save_bill'),
    path('bill/list/', GetBillListView.as_view(), name='get_bill_list'),
    path('bill/delete/', DeleteBillView.as_view(), name='delete_bill'),
]
