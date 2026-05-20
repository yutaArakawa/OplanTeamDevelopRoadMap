from django.urls import path
from inventory.views import (
    GoodsCategoryCreateView,
    GoodsCategoryDeleteView,
    GoodsCategoryListView,
    GoodsCategoryUpdateView,
    GoodsCreateView,
    GoodsDeleteView,
    GoodsListView,
    GoodsUpdateView,
)


urlpatterns = [
    path('goods-categories/', GoodsCategoryListView.as_view(), name='goods_category_list'),
    path('goods-categories/create/', GoodsCategoryCreateView.as_view(), name='goods_category_create'),
    path('goods-categories/<int:pk>/edit/', GoodsCategoryUpdateView.as_view(), name='goods_category_edit'),
    path('goods-categories/<int:pk>/delete/', GoodsCategoryDeleteView.as_view(), name='goods_category_delete'),
    path('goods/', GoodsListView.as_view(), name='goods_list'),
    path('goods/create/', GoodsCreateView.as_view(), name='goods_create'),
    path('goods/<int:pk>/edit/', GoodsUpdateView.as_view(), name='goods_edit'),
    path('goods/<int:pk>/delete/', GoodsDeleteView.as_view(), name='goods_delete'),
]
