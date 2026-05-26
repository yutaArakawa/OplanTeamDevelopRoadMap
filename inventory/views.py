import csv
import traceback
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, quote

from django.contrib import messages
from django.db.models import Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView, ListView
from django.http import HttpResponse

from common.mixins import AdminRequiredMixin, ShopStaffRequiredMixin, WarehouseStaffRequiredMixin

from inventory.forms import (
    GoodsCategoryForm,
    GoodsCreateForm,
    RelationForm,
    ShopForm,
    WarehouseCreateForm,
    WarehouseStockEditForm,
    OrderForm
)
from inventory.models import Goods, GoodsCategory, Relation, Warehouse, Shop, WarehouseStock, Order, OrderGoods

from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE

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


class ShopCreateView(AdminRequiredMixin, CreateView):
    template_name = 'inventory/shop_create.html'
    model = Shop
    form_class = ShopForm
    success_url = reverse_lazy('shop_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '店舗追加'
        context['submit_label'] = '登録'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '店舗を登録しました。')
        return response


class ShopUpdateView(AdminRequiredMixin, UpdateView):
    template_name = 'inventory/shop_create.html'
    model = Shop
    form_class = ShopForm
    success_url = reverse_lazy('shop_list')

    def get_queryset(self):
        return Shop.active_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '店舗編集'
        context['submit_label'] = '更新'
        context['can_delete'] = not self.object.has_related_records()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '店舗を更新しました。')
        return response


class ShopDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        shop = get_object_or_404(Shop.active_objects, pk=pk)

        if shop.has_related_records():
            messages.error(
                request,
                '在庫情報・倉庫店舗連携・所属ユーザー・集計データに紐づく店舗は削除できません。'
            )
            return redirect(request.POST.get('next') or reverse('shop_list'))

        shop.soft_delete()
        messages.success(request, '店舗を削除しました。')
        return redirect(request.POST.get('next') or reverse('shop_list'))

class WarehouseStockListView(WarehouseStaffRequiredMixin, TemplateView):
    template_name = 'inventory/warehouse_stock_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouse_stock_list = Goods.active_objects.select_related('goods_category').annotate(
            # レコードがあればそのままstock、なければ0で表示
            stock=Coalesce(
                Sum('warehousestock__stock', filter=Q(warehousestock__warehouse=self.request.user.warehouse)), 0
            )
        )
        categories = GoodsCategory.active_objects.all()

        category_query = self.request.GET.get('category')
        if category_query:
            warehouse_stock_list = warehouse_stock_list.filter(goods_category_id=category_query)

        context['selected_category'] = category_query
        context['categories'] = categories
        warehouse_stock_list = warehouse_stock_list.order_by('goods_name')
        context['warehouse_stock_list'] = warehouse_stock_list
        context['warehouse_name'] = self.request.user.warehouse.warehouse_name
        return context

class WarehouseStockEditView(WarehouseStaffRequiredMixin, TemplateView):
    model = WarehouseStock
    template_name = 'inventory/warehouse_stock_edit.html'
    success_url = reverse_lazy('warehouse_stock_list')

    def get(self, request, *args, **kwargs):
        goods = get_object_or_404(Goods, pk=kwargs['goods_pk'])
        # レコードがあればそのままstock、なければ0で表示
        warehouse_stock = WarehouseStock.objects.filter(
            goods=goods,
            warehouse=request.user.warehouse
        ).first()
        form = WarehouseStockEditForm(instance=warehouse_stock)
        context = self.get_context_data(**kwargs)
        context['form'] = form
        context['goods'] = goods
        context['page_title'] = '倉庫在庫編集'
        context['submit_label'] = '更新'
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        goods = get_object_or_404(Goods, pk=kwargs['goods_pk'])
        form = WarehouseStockEditForm(request.POST)
        if form.is_valid():
            stock_value = form.cleaned_data['stock']
            WarehouseStock.objects.update_or_create(
                goods=goods,
                warehouse=request.user.warehouse,
                defaults={'stock': stock_value}
            )
            return redirect('warehouse_stock_list')
        return render(request, self.template_name, {'form': form, 'goods': goods})

class RelationListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/relation_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop_name_query = self.request.GET.get('shop_name', '').strip()
        relation_qs = Relation.active_objects.select_related('warehouse').order_by(
            'warehouse__warehouse_name'
        )
        shops = Shop.active_objects.all()

        if shop_name_query:
            shops = shops.filter(shop_name__icontains=shop_name_query)

        context['selected_shop_name'] = shop_name_query
        context['shop_list'] = shops.order_by('shop_name').prefetch_related(
            Prefetch('relation_set', queryset=relation_qs, to_attr='active_relations')
        )
        return context


class RelationCreateView(AdminRequiredMixin, CreateView):
    template_name = 'inventory/relation_create.html'
    model = Relation
    form_class = RelationForm
    success_url = reverse_lazy('relation_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '連携倉庫追加'
        context['submit_label'] = '登録'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '連携倉庫を登録しました。')
        return response

class OrderGoodsListView(ShopStaffRequiredMixin, ListView):
    template_name = 'inventory/order_goods_list.html'
    context_object_name = 'order_goods_list'

    def get_queryset(self):
        # 連携倉庫の在庫合計を併せて取得
        related_warehouse_ids = Relation.objects.filter(
            shop=self.request.user.shop
        ).values_list('warehouse_id', flat=True)

        return Goods.active_objects.select_related('goods_category').annotate(
            # レコードがあればそのままstock、なければ0で表示
            stock=Coalesce(
                Sum(
                    'warehousestock__stock',
                    filter=Q(warehousestock__warehouse_id__in=related_warehouse_ids)
                ),
                0
            )
        ).order_by('goods_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ログインユーザーの店舗と連携している倉庫IDを取得
        related_warehouse_ids = Relation.objects.filter(
            shop=self.request.user.shop
        ).values_list('warehouse_id', flat=True)

        select_goods_list = Goods.active_objects.select_related('goods_category').annotate(
            # レコードがあればそのままstock、なければ0で表示
            stock=Coalesce(
                Sum(
                    'warehousestock__stock',
                    filter=Q(warehousestock__warehouse_id__in=related_warehouse_ids)
                ),
                0
            )
        )
        categories = GoodsCategory.active_objects.all()

        category_query = self.request.GET.get('category')
        if category_query:
            select_goods_list = select_goods_list.filter(goods_category_id=category_query)

        context['categories'] = categories
        context['selected_category'] = category_query
        select_goods_list = select_goods_list.order_by('goods_name')
        context['select_goods_list'] = select_goods_list
        return context

class OrderCreateView(ShopStaffRequiredMixin, TemplateView):
    template_name = 'inventory/order_create.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.goods = get_object_or_404(Goods, pk=self.kwargs['goods_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        relations = Relation.active_objects.filter(
            shop=self.request.user.shop
        ).select_related('warehouse').annotate(
            warehouse_stock=Coalesce(
                Sum('warehouse__warehousestock__stock',
                    filter=Q(warehouse__warehousestock__goods=self.goods)),
                0
            )
        )
        context['page_title'] = '発注画面'
        context['submit_label'] = '発注'
        context['goods'] = self.goods
        context['relations'] = relations
        return context
    
    def post(self, request, *args, **kwargs):
        relations = Relation.active_objects.filter(
            shop=request.user.shop
        ).select_related('warehouse')

        for relation in relations:
            form = OrderForm({'quantity': request.POST.get(f'quantity_{relation.id}', 0)})
            if form.is_valid():
                quantity = form.cleaned_data['quantity']
                if quantity > 0:
                    order = Order.objects.create(relation=relation)
                    OrderGoods.objects.create(
                        order=order,
                        goods=self.goods,
                        quantity=quantity
                    )
        messages.success(self.request, '発注しました。')
        return redirect('order_goods_list')

class OrderCsvDownloadView(ShopStaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response.write('\ufeff')  # BOMの書き込み
        filename = "一括商品発注表.csv"
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"

        writer = csv.writer(response)
        writer.writerow(['倉庫ID', '倉庫名', 'カテゴリ', '商品ID', '商品名', '現在の在庫数', '発注数'])
        # ログインユーザーの店舗と連携している倉庫情報を取得
        related_warehouse_ids = Relation.objects.filter(
            shop=self.request.user.shop
        ).values_list('warehouse_id', flat=True)

        stocks = WarehouseStock.active_objects.select_related(
            'warehouse',
            'goods',
            'goods__goods_category',
        ).filter(
            warehouse_id__in=related_warehouse_ids
        ).order_by('warehouse__warehouse_name')

        for stock in stocks:
            writer.writerow([
                stock.warehouse.id,
                stock.warehouse.warehouse_name,
                stock.goods.goods_category.category_name,
                stock.goods.id,
                stock.goods.goods_name,
                stock.stock,
                ''  # 発注数は空欄で出力
            ])

        return response

class OrderCsvImportView(ShopStaffRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'CSVファイルが選択されていません。')
            return redirect('order_goods_list')

        try:
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file)

            orders = {}
            for row in reader:
                warehouse_id = row['倉庫ID'].strip()
                goods_id = row['商品ID'].strip()
                order_quantity_str = row['発注数'].strip()
                if not order_quantity_str:
                    continue
                order_quantity = int(order_quantity_str)
                if order_quantity > 0:
                    warehouse = Warehouse.active_objects.filter(id=warehouse_id).first()
                    goods = Goods.active_objects.filter(id=goods_id).first()

                    if warehouse and goods:
                        relation = Relation.active_objects.filter(
                            shop=request.user.shop,
                            warehouse=warehouse
                        ).first()
                        if relation:
                            # 同一倉庫のOrderがすでに存在する場合は新たにOrderを作成せず、既存のOrderにOrderGoodsを追加する
                            if relation.id not in orders:
                                orders[relation.id] = Order.objects.create(relation=relation)

                            order = orders[relation.id]
                            OrderGoods.objects.create(
                                order=order,
                                goods=goods,
                                quantity=order_quantity
                            )
            messages.success(request, 'CSVファイルから発注を作成しました。')
        except Exception as e:
            messages.error(request, f'CSVファイルの処理中にエラーが発生しました: {str(e)}')
            traceback.print_exc()

        return redirect('order_goods_list')

class WarehouseOrderListView(WarehouseStaffRequiredMixin, TemplateView):
    template_name = 'inventory/warehouse_order_list.html'

    def _get_filtered_orders(self):
        qs = (
            Order.active_objects
            .filter(relation__warehouse=self.request.user.warehouse)
            .select_related('relation__shop')
            .prefetch_related(
                Prefetch(
                    'ordergoods_set',
                    queryset=OrderGoods.active_objects.select_related('goods').order_by('goods__goods_name'),
                    to_attr='active_order_goods',
                )
            )
            .order_by('-ordered_at')
        )

        date_from = self.request.GET.get('date_from', '').strip()
        date_to   = self.request.GET.get('date_to',   '').strip()
        status    = self.request.GET.get('status',    '').strip()

        if date_from:
            qs = qs.filter(ordered_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(ordered_at__date__lte=date_to)
        if status != '':
            try:
                qs = qs.filter(status=int(status))
            except (ValueError, TypeError):
                pass

        return qs

    def _build_rows(self, orders):
        rows = []
        for order in orders:
            goods_list = order.active_order_goods
            count = len(goods_list)
            if count == 0:
                rows.append({'order': order, 'order_goods': None, 'is_first': True, 'goods_count': 1})
            else:
                for i, og in enumerate(goods_list):
                    rows.append({'order': order, 'order_goods': og, 'is_first': i == 0, 'goods_count': count})
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = self._get_filtered_orders()
        context['rows']            = self._build_rows(orders)
        context['status_choices']  = Order.Status.choices
        context['selected_status'] = self.request.GET.get('status',    '')
        context['date_from']       = self.request.GET.get('date_from', '')
        context['date_to']         = self.request.GET.get('date_to',   '')
        return context


class WarehouseOrderStatusUpdateView(WarehouseStaffRequiredMixin, View):

    ALLOWED_STATUSES = {Order.Status.ORDERED.value, Order.Status.PREPARING.value}

    def post(self, request, pk):
        order = get_object_or_404(
            Order.active_objects,
            pk=pk,
            relation__warehouse=request.user.warehouse,
        )
        new_status = request.POST.get('status', '').strip()
        try:
            new_status_int = int(new_status)
            if new_status_int not in self.ALLOWED_STATUSES:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, '無効なステータスです。')
            return redirect(request.POST.get('next') or reverse('warehouse_order_list'))

        order.status = new_status_int
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'ステータスを更新しました。')
        return redirect(request.POST.get('next') or reverse('warehouse_order_list'))
    
    
