from django.urls import path
from inventory.views import GoodsCreateView, GoodsDeleteView, GoodsListView


urlpatterns = [
    path('goods/', GoodsListView.as_view(), name='goods_list'),
    path('goods/create/', GoodsCreateView.as_view(), name='goods_create'),
    path('goods/<int:pk>/delete/', GoodsDeleteView.as_view(), name='goods_delete'),
]
