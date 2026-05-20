from django.views.generic import TemplateView

from common.mixins import AdminRequiredMixin

from .models import Shop


class ShopListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/shop_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shops = Shop.active_objects.all().order_by('id')
        context['shops'] = shops
        return context
