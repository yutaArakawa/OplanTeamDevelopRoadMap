import json
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views import View
from common.api_constants import ApiStatus, ApiErrorMsg, ApiResponseStatus

class MeAPIView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': ApiErrorMsg.UNAUTHORIZED},
                status=ApiResponseStatus.UNAUTHORIZED
            )
        return JsonResponse({
            'username': request.user.username,
            'authority': request.user.authority_id,
            'authority_name': request.user.authority.authority_name,
            'shop': request.user.shop.shop_name if request.user.shop else None,
            'warehouse': request.user.warehouse.warehouse_name if request.user.warehouse else None,
        })

class CsrfAPIView(View):
    def get(self, request):
        return JsonResponse({'csrfToken':get_token(request)})

class LoginAPIView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return JsonResponse(
                {'error': ApiErrorMsg.REQUIRED_FIELDS_LOGIN},
                status=ApiResponseStatus.BAD_REQUEST
            )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            return JsonResponse(
                {'error': ApiErrorMsg.ACCOUNT_INVALID},
                status=ApiResponseStatus.UNAUTHORIZED
            )

        if user.delete_flg:
            return JsonResponse(
                {'error': ApiErrorMsg.ACCOUNT_DELETED},
                status=ApiResponseStatus.UNAUTHORIZED
            )

        login(request, user)
        return JsonResponse({'status': ApiStatus.OK}, status=ApiResponseStatus.OK)

class LogoutAPIView(View):
    def post(self, request):
        logout(request)
        return JsonResponse({'status': ApiStatus.OK}, status=ApiResponseStatus.OK)
