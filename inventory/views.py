from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView

from common.mixins import AdminRequiredMixin
from inventory.models import Warehouse


class WarehouseListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/warehouse_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        warehouses = Warehouse.active_objects.all()
        address_query = self.request.GET.get('address', '').strip()

        if address_query:
            warehouses = warehouses.filter(
                Q(prefecture__icontains=address_query)
                | Q(city__icontains=address_query)
                | Q(address1__icontains=address_query)
                | Q(address2__icontains=address_query)
            )

        context['warehouse_list'] = warehouses.order_by('warehouse_name')
        context['selected_address'] = address_query
        return context


class WarehouseCreateView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/warehouse_form_placeholder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '倉庫追加'
        return context


class WarehouseUpdateView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/warehouse_form_placeholder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouse = get_object_or_404(Warehouse.active_objects, pk=self.kwargs['pk'])
        context['page_title'] = '倉庫編集'
        context['warehouse'] = warehouse
        return context


class WarehouseDeleteView(AdminRequiredMixin, View):
    success_url = reverse_lazy('warehouse_list')

    def post(self, request, pk):
        warehouse = get_object_or_404(Warehouse.active_objects, pk=pk)
        warehouse.soft_delete()
        messages.success(request, '倉庫を削除しました。')
        return redirect(request.POST.get('next') or reverse('warehouse_list'))
