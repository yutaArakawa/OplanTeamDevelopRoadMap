from django.contrib.auth.mixins import LoginRequiredMixin
from common.constants import (AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE)
from common.exceptions import ForbiddenException

# 管理者
class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.authority_id != AUTHORITY_ADMIN:
            raise ForbiddenException
        return super().dispatch(request, *args, **kwargs)

# 店舗スタッフ
class ShopStaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.authority_id != AUTHORITY_SHOP:
            raise ForbiddenException
        return super().dispatch(request, *args, **kwargs)

# 倉庫スタッフ
class WarehouseStaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.authority_id != AUTHORITY_WAREHOUSE:
            raise ForbiddenException
        return super().dispatch(request, *args, **kwargs)