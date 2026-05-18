from django.views.generic import TemplateView

from common.mixins import AdminRequiredMixin
from inventory.models import Goods, GoodsCategory


class GoodsListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/goods_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        goods = Goods.objects.select_related('goods_category').all()
        category_id = self.request.GET.get('category')

        if category_id:
            goods = goods.filter(goods_category_id=category_id)

        context['goods_list'] = goods.order_by('goods_name')
        context['categories'] = GoodsCategory.objects.all().order_by('category_name')
        context['selected_category'] = category_id or ''
        return context


class GoodsCreateView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/goods_create.html'
