from django.urls import path
from inventory.views import (
    WarehouseCreateView,
    WarehouseDeleteView,
    WarehouseListView,
    WarehouseUpdateView,
)

urlpatterns = [
    path('warehouses/', WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/create/', WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', WarehouseUpdateView.as_view(), name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', WarehouseDeleteView.as_view(), name='warehouse_delete'),
]
