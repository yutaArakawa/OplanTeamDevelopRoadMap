import json
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views import View
from common.api_constants import ApiStatus, ApiErrorMsg, ApiResponseStatus
from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE
from inventory.models import Goods, GoodsCategory, Order, Shop, Warehouse
from accounts.models import User
from accounts import services

class UserListAPIView(View):

    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': ApiErrorMsg.UNAUTHORIZED},
                status=ApiResponseStatus.UNAUTHORIZED
            )
        user = request.user
        if user.authority_id == AUTHORITY_SHOP:
            affiliation = user.shop
        elif user.authority_id == AUTHORITY_WAREHOUSE:
            affiliation = user.warehouse
        else:
            affiliation = None

        qs = services.getUserList(user.authority_id, affiliation)

        # 絞り込みパラメータ
        filter_authority = request.GET.get('authority')
        filter_shop = request.GET.get('shop')
        filter_warehouse = request.GET.get('warehouse')

        if filter_authority:
            qs = qs.filter(authority_id=filter_authority)
        if filter_shop:
            qs = qs.filter(shop_id=filter_shop)
        if filter_warehouse:
            qs = qs.filter(warehouse_id=filter_warehouse)

        users = list(
            qs.order_by('username').values(
                'id',
                'username',
                'user_gender',
                'authority_id',
                'authority__authority_name',
                'shop__shop_name',
                'warehouse__warehouse_name'
            )
        )

        # フィルター用の選択肢（管理者のみ全店舗・倉庫を返す）
        authorities = []
        shops = []
        warehouses = []
        if user.authority_id == AUTHORITY_ADMIN:
            from accounts.models import Authority
            authorities = list(Authority.objects.values('id', 'authority_name'))
            shops = list(Shop.active_objects.values('id', 'shop_name'))
            warehouses = list(Warehouse.active_objects.values('id', 'warehouse_name'))

        return JsonResponse({
            'users': users,
            'authorities': authorities,
            'shops': shops,
            'warehouses': warehouses,
        })
