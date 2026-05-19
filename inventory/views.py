from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from common.mixins import AdminRequiredMixin
from inventory.models import Goods, GoodsCategory

class GoodsListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/goods_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        goods = Goods.active_objects.select_related('goods_category').all()
        category_id = self.request.GET.get('category')

        if category_id:
            goods = goods.filter(goods_category_id=category_id)

        goods_list = list(goods.order_by('goods_name'))
        for goods_item in goods_list:
            goods_item.can_delete = not goods_item.has_related_records()

        context['goods_list'] = goods_list
        context['categories'] = GoodsCategory.active_objects.all().order_by('category_name')
        context['selected_category'] = category_id or ''
        return context


class GoodsCreateView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/goods_create.html'


class GoodsDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        goods = get_object_or_404(Goods.active_objects, pk=pk)

        if goods.has_related_records():
            messages.error(
                request,
                '在庫情報または受注明細に紐づく商品のため削除できません。'
            )
            return redirect(request.POST.get('next') or reverse('goods_list'))

        goods.soft_delete()
        messages.success(request, '商品を削除しました。')
        return redirect(request.POST.get('next') or reverse('goods_list'))
