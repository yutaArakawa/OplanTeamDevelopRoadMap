from django.contrib import admin

# Register your models here.
from .models import User, Shop, Warehouse, Authority, GoodsCategory, Goods, ShopStock, WarehouseStock, Relation, Order, OrderGoods, Inquiry, MonthlyOrderSummary 

admin.site.register(User)
admin.site.register(Shop)
admin.site.register(Warehouse)
admin.site.register(Authority)
admin.site.register(GoodsCategory)
admin.site.register(Goods)
admin.site.register(ShopStock)
admin.site.register(WarehouseStock)
admin.site.register(Relation)
admin.site.register(Order)
admin.site.register(OrderGoods)
admin.site.register(Inquiry)
admin.site.register(MonthlyOrderSummary)