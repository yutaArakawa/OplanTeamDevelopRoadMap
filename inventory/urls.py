from django.urls import path

from .views import ShopListView


urlpatterns = [
    path(
        'shop_list/',
        ShopListView.as_view(),
        name='shop_list'
    ),
]
