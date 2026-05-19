from django.contrib import admin

# Register your models here.
from .models import Shop, Warehouse, GoodsCategory, Goods, ShopStock, WarehouseStock, Relation, Order, OrderGoods

admin.site.register(Shop)
admin.site.register(Warehouse)
admin.site.register(GoodsCategory)
admin.site.register(Goods)
admin.site.register(ShopStock)
admin.site.register(WarehouseStock)
admin.site.register(Relation)
admin.site.register(Order)
admin.site.register(OrderGoods)