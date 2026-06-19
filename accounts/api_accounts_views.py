import json
from django.http import JsonResponse
from django.views import View
from common.api_constants import ApiStatus, ApiErrorMsg, ApiResponseStatus
from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE
from accounts import services, validators


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
        filter_shop      = request.GET.get('shop')
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

        # フィルター用の選択肢（管理者のみ）
        authorities, shops, warehouses = [], [], []
        if user.authority_id == AUTHORITY_ADMIN:
            authorities, shops, warehouses = services.getFilterOptions()

        return JsonResponse({
            'users': users,
            'authorities': authorities,
            'shops': shops,
            'warehouses': warehouses,
        })


class UserCreateAPIView(View):

    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': ApiErrorMsg.UNAUTHORIZED}, status=ApiResponseStatus.UNAUTHORIZED)

        authorities, shops, warehouses = services.getFormOptions(request.user)
        return JsonResponse({'authorities': authorities, 'shops': shops, 'warehouses': warehouses})

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': ApiErrorMsg.UNAUTHORIZED}, status=ApiResponseStatus.UNAUTHORIZED)

        if request.user.authority_id != AUTHORITY_ADMIN:
            return JsonResponse({'error': 'この操作は管理者のみ実行できます'}, status=ApiResponseStatus.FORBIDDEN)

        data = json.loads(request.body)
        username     = data.get('username', '').strip()
        password1    = data.get('password1', '')
        password2    = data.get('password2', '')
        user_gender  = data.get('user_gender')
        authority    = data.get('authority')
        shop_id      = data.get('shop') or None
        warehouse_id = data.get('warehouse') or None

        errors = {
            **validators.validate_user_fields(username, user_gender, authority, shop_id, warehouse_id),
            **validators.validate_password(password1, password2, required=True),
        }
        if errors:
            return JsonResponse({'errors': errors}, status=ApiResponseStatus.BAD_REQUEST)

        try:
            services.createUser(username, password1, user_gender, authority, shop_id, warehouse_id)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=ApiResponseStatus.INTERNAL_SERVER_ERROR)

        return JsonResponse({'status': ApiStatus.OK}, status=ApiResponseStatus.OK)


class UserDetailAPIView(View):

    def get(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({'error': ApiErrorMsg.UNAUTHORIZED}, status=ApiResponseStatus.UNAUTHORIZED)

        user = services.getUser(pk)
        if user is None:
            return JsonResponse({'error': 'ユーザーが見つかりません'}, status=ApiResponseStatus.NOT_FOUND)

        authorities, shops, warehouses = services.getFormOptions(request.user)

        return JsonResponse({
            'user': {
                'id':           user.id,
                'username':     user.username,
                'user_gender':  user.user_gender,
                'authority':    user.authority_id,
                'shop':         user.shop_id,
                'warehouse':    user.warehouse_id,
            },
            'authorities': authorities,
            'shops':       shops,
            'warehouses':  warehouses,
        })

    def put(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({'error': ApiErrorMsg.UNAUTHORIZED}, status=ApiResponseStatus.UNAUTHORIZED)

        user = services.getUser(pk)
        if user is None:
            return JsonResponse({'error': 'ユーザーが見つかりません'}, status=ApiResponseStatus.NOT_FOUND)

        data = json.loads(request.body)
        errors = {}

        if request.user.authority_id == AUTHORITY_ADMIN:
            username     = data.get('username', '').strip()
            user_gender  = data.get('user_gender')
            authority    = data.get('authority')
            shop_id      = data.get('shop') or None
            warehouse_id = data.get('warehouse') or None

            errors.update(validators.validate_user_fields(
                username, user_gender, authority, shop_id, warehouse_id, exclude_pk=pk
            ))
            update_fields = dict(
                username=username,
                user_gender=user_gender,
                authority_id=authority,
                shop_id=shop_id,
                warehouse_id=warehouse_id,
            )
        else:
            shop_id      = data.get('shop') or None
            warehouse_id = data.get('warehouse') or None
            update_fields = dict(shop_id=shop_id, warehouse_id=warehouse_id)

        password1 = data.get('new_password1', '')
        password2 = data.get('new_password2', '')
        pw_errors = validators.validate_password(password1, password2, required=False)
        if 'password1' in pw_errors:
            errors['new_password1'] = pw_errors['password1']
        if 'password2' in pw_errors:
            errors['new_password2'] = pw_errors['password2']

        if errors:
            return JsonResponse({'errors': errors}, status=ApiResponseStatus.BAD_REQUEST)

        try:
            services.updateUser(user, password=password1 or None, **update_fields)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=ApiResponseStatus.INTERNAL_SERVER_ERROR)

        return JsonResponse({'status': ApiStatus.OK})

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({'error': ApiErrorMsg.UNAUTHORIZED}, status=ApiResponseStatus.UNAUTHORIZED)

        if request.user.authority_id != AUTHORITY_ADMIN:
            return JsonResponse({'error': 'この操作は管理者のみ実行できます'}, status=ApiResponseStatus.FORBIDDEN)

        user = services.getUser(pk)
        if user is None:
            return JsonResponse({'error': 'ユーザーが見つかりません'}, status=ApiResponseStatus.NOT_FOUND)

        if user == request.user:
            return JsonResponse({'error': '自分自身は削除できません'}, status=ApiResponseStatus.BAD_REQUEST)

        try:
            services.deleteUser(user)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=ApiResponseStatus.INTERNAL_SERVER_ERROR)

        return JsonResponse({'status': ApiStatus.OK})
