from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from common.constants import (AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE)

# 管理者
class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.authority_id != AUTHORITY_ADMIN:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

# 店舗スタッフ
class ShopStaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.authority_id != AUTHORITY_SHOP:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

# 倉庫スタッフ
class WarehouseStaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.authority_id != AUTHORITY_WAREHOUSE:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)