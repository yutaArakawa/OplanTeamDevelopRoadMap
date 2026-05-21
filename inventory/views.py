from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView, TemplateView

from common.mixins import AdminRequiredMixin

from inventory.forms import GoodsCategoryForm, GoodsCreateForm, WarehouseCreateForm
from inventory.models import Goods, GoodsCategory, Warehouse, Shop


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


class WarehouseCreateView(AdminRequiredMixin, CreateView):
    template_name = 'inventory/warehouse_create.html'
    model = Warehouse
    form_class = WarehouseCreateForm
    success_url = reverse_lazy('warehouse_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '倉庫追加'
        context['submit_label'] = '登録'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '倉庫を登録しました。')
        return response


class WarehouseUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'inventory/warehouse_create.html'
    model = Warehouse
    form_class = WarehouseCreateForm
    success_url = reverse_lazy('warehouse_list')

    def get_queryset(self):
        return Warehouse.active_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '倉庫編集'
        context['submit_label'] = '更新'
        context['can_delete'] = not self.object.has_related_records()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '倉庫を更新しました。')
        return response


class WarehouseDeleteView(AdminRequiredMixin, View):
    success_url = reverse_lazy('warehouse_list')

    def post(self, request, pk):
        warehouse = get_object_or_404(Warehouse.active_objects, pk=pk)

        if warehouse.has_related_records():
            messages.error(
                request,
                '在庫情報・倉庫店舗連携・所属ユーザーに紐づく倉庫は削除できません。'
            )
            return redirect(request.POST.get('next') or reverse('warehouse_list'))

        warehouse.soft_delete()
        messages.success(request, '倉庫を削除しました。')
        return redirect(request.POST.get('next') or reverse('warehouse_list'))

class GoodsCategoryListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/goods_category_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_list'] = GoodsCategory.active_objects.order_by('category_name')
        return context

      
class GoodsCategoryCreateView(AdminRequiredMixin, CreateView):
    template_name = 'inventory/goods_category_create.html'
    model = GoodsCategory
    form_class = GoodsCategoryForm
    success_url = reverse_lazy('goods_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '商品カテゴリ作成'
        context['submit_label'] = '登録'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '商品カテゴリを登録しました。')
        return response

    def form_invalid(self, form):
        next_url = self.request.POST.get('next')
        if next_url:
            category_name_errors = form.errors.get('category_name')
            if category_name_errors:
                messages.error(self.request, category_name_errors[0])
            else:
                messages.error(self.request, '商品カテゴリを登録できませんでした。')
            return redirect(next_url)
        return super().form_invalid(form)

    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if not next_url:
            return super().get_success_url()

        parsed_url = urlsplit(next_url)
        query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
        query_params['category_created'] = str(self.object.pk)
        return urlunsplit((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            urlencode(query_params),
            parsed_url.fragment,
        ))


class GoodsCategoryUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'inventory/goods_category_create.html'
    model = GoodsCategory
    form_class = GoodsCategoryForm
    success_url = reverse_lazy('goods_category_list')

    def get_queryset(self):
        return GoodsCategory.active_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '商品カテゴリ編集'
        context['submit_label'] = '更新'
        context['can_delete'] = not self.object.has_related_records()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '商品カテゴリを更新しました。')
        return response


class GoodsCategoryDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        category = get_object_or_404(GoodsCategory.active_objects, pk=pk)

        if category.has_related_records():
            messages.error(
                request,
                '商品に紐づくカテゴリのため削除できません。'
            )
            return redirect(request.POST.get('next') or reverse('goods_category_list'))

        category.soft_delete()
        messages.success(request, '商品カテゴリを削除しました。')
        return redirect(request.POST.get('next') or reverse('goods_category_list'))


class GoodsListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/goods_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        goods = Goods.active_objects.select_related('goods_category').all()
        category_id = self.request.GET.get('category')

        if category_id:
            try:
                category_id = int(category_id)
                goods = goods.filter(goods_category_id=category_id)
            except (TypeError, ValueError):
                category_id = ''

        context['goods_list'] = goods.order_by('goods_name')
        context['categories'] = GoodsCategory.active_objects.all().order_by('category_name')
        context['selected_category'] = category_id or ''
        return context

class GoodsCreateView(AdminRequiredMixin, CreateView):
    template_name = 'inventory/goods_create.html'
    model = Goods
    form_class = GoodsCreateForm
    success_url = reverse_lazy('goods_list')

    def get_initial(self):
        initial = super().get_initial()
        created_category_id = self.request.GET.get('category_created')
        if created_category_id:
            initial['goods_category'] = created_category_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '商品作成'
        context['submit_label'] = '登録'
        context['category_form'] = GoodsCategoryForm()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '商品を登録しました。')
        return response

      
class GoodsUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'inventory/goods_create.html'
    model = Goods
    form_class = GoodsCreateForm
    success_url = reverse_lazy('goods_list')

    def get_queryset(self):
        return Goods.active_objects.all()

    def get_initial(self):
        initial = super().get_initial()
        created_category_id = self.request.GET.get('category_created')
        if created_category_id:
            initial['goods_category'] = created_category_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '商品編集'
        context['submit_label'] = '更新'
        context['can_delete'] = not self.object.has_related_records()
        context['category_form'] = GoodsCategoryForm()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '商品を更新しました。')
        return response

      
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
    

class ShopListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/shop_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shops = Shop.active_objects.all()
        address_query = self.request.GET.get('address', '').strip()

        if address_query:
            shops = shops.filter(
                Q(prefecture__icontains=address_query)
                | Q(city__icontains=address_query)
                | Q(address1__icontains=address_query)
                | Q(address2__icontains=address_query)
            )

        context['selected_address'] = address_query
        shops = shops.order_by('shop_name')
        context['shops'] = shops
        return context


class ShopCreatePlaceholderView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/shop_create_placeholder.html'


class ShopUpdatePlaceholderView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/shop_edit_placeholder.html'
