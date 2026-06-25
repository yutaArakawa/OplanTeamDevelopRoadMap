from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated, PermissionDenied as DRFPermissionDenied
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404

HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_500_INTERNAL_SERVER_ERROR = 500


class BadRequestException(Exception):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = 'リクエストが不正です。'


class UnauthorizedException(Exception):
    status_code = HTTP_401_UNAUTHORIZED
    default_detail = '認証情報が含まれていません。'


class ForbiddenException(DjangoPermissionDenied):
    # DjangoのHTMLビューでも403として処理されるようDjangoPermissionDeniedを継承
    status_code = HTTP_403_FORBIDDEN
    default_detail = 'このリソースへのアクセス権限がありません。'


class NotFoundException(Exception):
    status_code = HTTP_404_NOT_FOUND
    default_detail = 'リソースが見つかりません。'


def custom_exception_handler(exc, context):
    # カスタム例外をDRFの形式に変換
    if isinstance(exc, BadRequestException):
        return Response(
            {'status_code': HTTP_400_BAD_REQUEST, 'detail': str(exc) or exc.default_detail},
            status=HTTP_400_BAD_REQUEST
        )
    if isinstance(exc, UnauthorizedException):
        return Response(
            {'status_code': HTTP_401_UNAUTHORIZED, 'detail': str(exc) or exc.default_detail},
            status=HTTP_401_UNAUTHORIZED
        )
    if isinstance(exc, (ForbiddenException, DjangoPermissionDenied)):
        return Response(
            {'status_code': HTTP_403_FORBIDDEN, 'detail': ForbiddenException.default_detail},
            status=HTTP_403_FORBIDDEN
        )
    if isinstance(exc, (NotFoundException, Http404)):
        return Response(
            {'status_code': HTTP_404_NOT_FOUND, 'detail': NotFoundException.default_detail},
            status=HTTP_404_NOT_FOUND
        )

    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {'status_code': HTTP_500_INTERNAL_SERVER_ERROR, 'detail': 'サーバーエラーが発生しました。'},
            status=HTTP_500_INTERNAL_SERVER_ERROR
        )

    # NotAuthenticated（未認証）は401に統一
    if isinstance(exc, NotAuthenticated):
        response.status_code = HTTP_401_UNAUTHORIZED

    response.data = {
        'status_code': response.status_code,
        'detail': response.data.get('detail', 'エラーが発生しました。'),
    }

    return response
