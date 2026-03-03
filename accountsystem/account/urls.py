from django.urls import path
from .views import (
    GetIconsView, SaveBillView, GetBillListView, DeleteBillView, 
    GetBillSummaryView, SaveBudgetView, GetBudgetView
)

urlpatterns = [
    path('icons/', GetIconsView.as_view(), name='get_icons'),
    path('bill/save/', SaveBillView.as_view(), name='save_bill'),
    path('bill/list/', GetBillListView.as_view(), name='get_bill_list'),
    path('bill/delete/', DeleteBillView.as_view(), name='delete_bill'),
    path('bill/summary/', GetBillSummaryView.as_view(), name='get_bill_summary'),
    path('budget/save/', SaveBudgetView.as_view(), name='save_budget'),
    path('budget/get/', GetBudgetView.as_view(), name='get_budget'),
]
