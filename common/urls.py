from django.urls import path
from common.views import (
    ShopNameAutoCompleteView,
    WarehouseNameAutoCompleteView,
    PrefectureNameAutoCompleteView,
)

urlpatterns = [
    path('api/shops/autocomplete/', ShopNameAutoCompleteView.as_view(), name='shop_name_autocomplete'),
    path('api/warehouses/autocomplete/', WarehouseNameAutoCompleteView.as_view(), name='warehouse_name_autocomplete'),
    path('api/prefecture/autocomplete/', PrefectureNameAutoCompleteView.as_view(), name='prefecture_name_autocomplete')
]