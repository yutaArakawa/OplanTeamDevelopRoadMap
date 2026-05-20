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
    add_warehouse_management,
    WarehouseCreateView,
    WarehouseDeleteView,
    WarehouseListView,
    WarehouseUpdateView,
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
    path('warehouses/', WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/create/', WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', WarehouseUpdateView.as_view(), name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', WarehouseDeleteView.as_view(), name='warehouse_delete'),
)