import json
from datetime import timedelta
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE
from common.api_constants import ApiStatus, ApiErrorMsg, ApiResponseStatus
from inventory.models import Goods, GoodsCategory, Order, Shop, Warehouse, WarehouseStock
from accounts.models import User
from dashboard.models import MonthlyOrderSummary
from dashboard import services

class HomeAPIView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': ApiErrorMsg.UNAUTHORIZED},
                status=ApiResponseStatus.UNAUTHORIZED
            )

        user = request.user

        if user.authority_id == AUTHORITY_ADMIN:
            data = {
                'warehoues_count': Warehouse.active_objects.count(),
                'shop_count': Shop.active_objects.count(),
                'goods_count': Goods.active_objects.count(),
                'category_count': GoodsCategory.active_objects.count(),
                'user_count': User.active_objects.filter(delete_flg=False).count(),
                'pending_order_count': Order.active_objects.filter(
                    status=Order.Status.ORDERED
                ).count(),
            }

        elif user.authority_id == AUTHORITY_SHOP:
            yesterday = timezone.now().date() - timedelta(days=1)
            if MonthlyOrderSummary.active_objects.filter(count_date=yesterday).exists():
                ranking_date = yesterday
            else:
                ranking_date = services.get_latest_summary_date()

            if ranking_date:
                shop_ranking = list(services.get_order_ranking(
                    services.get_monthly_order_summary(ranking_date, shop=user.shop)
                ))
                all_ranking = list(services.get_order_ranking(
                    services.get_monthly_order_summary(ranking_date)
                ))
            else:
                shop_ranking = []
                all_ranking = []

            data = {
                'shop_ranking': shop_ranking,
                'all_shop_ranking': all_ranking,
                'ranking_date': str(ranking_date) if ranking_date else None,
            }

        elif user.authority_id == AUTHORITY_WAREHOUSE:
            warehouse_stocks = WarehouseStock.active_objects.filter(
                warehouse=user.warehouse
            ).select_related('goods').order_by('goods__goods_name')

            data = {
                'stock_count': warehouse_stocks.count(),
                'new_order_count': Order.active_objects.filter(
                    relation__warehouse=user.warehouse,
                    status=Order.Status.ORDERED
                ).count(),
                'preparing_order_count': Order.active_objects.filter(
                    relation__warehouse=user.warehouse,
                    status=Order.Status.PREPARING
                ).count(),
                'warehouse_stocks': list(warehouse_stocks.values(
                    'goods__goods_name', 'stock'
                )),
            }

        return JsonResponse(data)
