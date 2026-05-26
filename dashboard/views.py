from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import User
from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE
from inventory.models import (
    Goods, GoodsCategory, Order, OrderGoods, Shop, ShopStock, Warehouse, WarehouseStock
)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.authority_id == AUTHORITY_ADMIN:
            context['warehouse_count'] = Warehouse.active_objects.count()
            context['shop_count'] = Shop.active_objects.count()
            context['goods_count'] = Goods.active_objects.count()
            context['category_count'] = GoodsCategory.active_objects.count()
            context['user_count'] = User.active_objects.filter(delete_flg=False).count()
            context['pending_order_count'] = Order.active_objects.filter(
                status=Order.Status.ORDERED
            ).count()

        elif user.authority_id == AUTHORITY_SHOP:
            one_month_ago = timezone.now() - timedelta(days=30)
            context['shop_ranking'] = (
                OrderGoods.active_objects
                .filter(
                    order__relation__shop=user.shop,
                    order__ordered_at__gte=one_month_ago
                )
                .values('goods__goods_name')
                .annotate(total=Sum('quantity'))
                .order_by('-total')[:10]
            )
            context['all_shop_ranking'] = (
                OrderGoods.active_objects
                .filter(order__ordered_at__gte=one_month_ago)
                .values('goods__goods_name')
                .annotate(total=Sum('quantity'))
                .order_by('-total')[:10]
            )

        elif user.authority_id == AUTHORITY_WAREHOUSE:
            warehouse_stocks = WarehouseStock.active_objects.filter(
                warehouse=user.warehouse
            ).select_related('goods').order_by('goods__goods_name')
            context['warehouse_stocks'] = warehouse_stocks
            context['stock_count'] = warehouse_stocks.count()
            context['new_order_count'] = Order.active_objects.filter(
                relation__warehouse=user.warehouse,
                status=Order.Status.ORDERED
            ).count()
            context['preparing_order_count'] = Order.active_objects.filter(
                relation__warehouse=user.warehouse,
                status=Order.Status.PREPARING
            ).count()

        return context