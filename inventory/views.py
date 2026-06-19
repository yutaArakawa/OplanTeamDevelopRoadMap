import csv
import traceback
import logging

from io import BytesIO
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, quote

from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView, ListView
from django.http import HttpResponse
from common.mixins import AdminRequiredMixin, ShopStaffRequiredMixin, WarehouseStaffRequiredMixin
from .services import minus_stock, restore_stock, add_shop_stock, subtract_shop_stock

from inventory.forms import (
    GoodsCategoryForm,
    GoodsCreateForm,
    RelationForm,
    ShopForm,
    ShopStockEditForm,
    WarehouseCreateForm,
    WarehouseStockEditForm,
    OrderForm
)
from inventory.models import Goods, GoodsCategory, Relation, Warehouse, Shop, WarehouseStock, ShopStock, Order, OrderGoods
from inventory.constants.prefectures import PREFECTURE_CHOICES
from inventory import services

from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE

logger = logging.getLogger(__name__)

class WarehouseListView(AdminRequiredMixin, TemplateView):
    template_name = 'inventory/warehouse_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        warehouses = Warehouse.active_objects.all()
        selected_prefecture = self.request.GET.get('prefecture', '')

        if selected_prefecture:
            warehouses = warehouses.filter(prefecture=selected_prefecture)

        context['warehouse_list'] = warehouses.order_by('warehouse_name')
        context['selected_prefecture'] = selected_prefecture
        context['prefecture_choices'] = PREFECTURE_CHOICES
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
        try:
            with transaction.atomic():
                goods_list = list(Goods.active_objects.select_for_update().all())
                response = super().form_valid(form)
                warehouse = self.object
                WarehouseStock.objects.bulk_create([
                    WarehouseStock(warehouse=warehouse, goods=goods, stock=0)
                    for goods in goods_list
                ])
            messages.success(self.request, '倉庫を登録しました。')
            return response
        except Exception as e:
            logger.error("Error occurred while creating warehouse: %s", str(e))
            messages.error(self.request, '倉庫の登録に失敗しました。')
            return super().form_invalid(form)

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
        try:
            with transaction.atomic():
                # 倉庫一覧をロック
                warehouses = list(Warehouse.active_objects.select_for_update().all())
                # 店舗一覧をロック
                shops      = list(Shop.active_objects.select_for_update().all())
                # 商品レコードを作成
                response = super().form_valid(form)
                # 倉庫在庫レコードを作成
                services.insert_initial_warehouse_stock_for_goods(self.object, warehouses)
                # 店舗在庫レコードを作成
                services.insert_initial_shop_stock_for_goods(self.object, shops)
            messages.success(self.request, '商品を登録しました。')
            return response
        except Exception as e:
            logger.error("Error occurred while creating goods: %s", str(e))
            messages.error(self.request, '商品の登録に失敗しました。')
            return super().form_invalid(form)
      
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
        selected_prefecture = self.request.GET.get('prefecture', '')

        if selected_prefecture:
            shops = shops.filter(prefecture=selected_prefecture)

        context['selected_prefecture'] = selected_prefecture
        context['prefecture_choices'] = PREFECTURE_CHOICES
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
        try:
            with transaction.atomic():
                goods_list = list(Goods.active_objects.select_for_update().all())
                response = super().form_valid(form)
                shop = self.object
                ShopStock.objects.bulk_create([
                    ShopStock(shop=shop, goods=goods, stock=0)
                    for goods in goods_list
                ])
            messages.success(self.request, '店舗を登録しました。')
            return response
        except Exception as e:
            logger.error("Error occurred while creating shop: %s", str(e))
            messages.error(self.request, '店舗の登録に失敗しました。')
            return super().form_invalid(form)

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

class ShopStockListView(ShopStaffRequiredMixin, TemplateView):
    template_name = 'inventory/shop_stock_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop_stock_list = services.get_shop_stock_list(self.request.user.shop)
        categories = services.get_goods_categories()

        category_query = self.request.GET.get('category')
        if category_query:
            shop_stock_list = shop_stock_list.filter(goods_category_id=category_query)

        context['selected_category'] = category_query
        context['categories'] = categories
        shop_stock_list = shop_stock_list.order_by('goods_name')
        context['shop_stock_list'] = shop_stock_list
        return context

class ShopStockEditView(ShopStaffRequiredMixin, TemplateView):
    template_name = 'inventory/shop_stock_edit.html'
    page_title = '店舗在庫編集'
    submit_label = '更新'

    def get(self, request, *args, **kwargs):
        goods = services.get_goods_by_goods_id(kwargs['goods_pk'])
        # レコードがあればそのままstock、なければ0で表示
        shop_stock = services.get_shop_stock_by_goods_and_shop(goods, request.user.shop)
        form = ShopStockEditForm(instance=shop_stock)
        context = self.get_context_data(**kwargs)
        context['form'] = form
        context['goods'] = goods
        context['page_title'] = self.page_title
        context['submit_label'] = self.submit_label
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        goods = services.get_goods_by_goods_id(kwargs['goods_pk'])
        form = ShopStockEditForm(request.POST)
        if form.is_valid():
            stock_value = form.cleaned_data['stock']
            services.update_or_create_shop_stock(goods, request.user.shop, stock_value)
            return redirect('shop_stock_list')
        return render(request, self.template_name, {
            'form': form,
            'goods': goods,
            'page_title': self.page_title,
            'submit_label': self.submit_label
        })

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

class ShopConnectedWarehouseListView(ShopStaffRequiredMixin, TemplateView):
    template_name = 'inventory/shop_connected_warehouse_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        relations = Relation.active_objects.select_related('warehouse').filter(
            shop=self.request.user.shop
        ).order_by('warehouse__warehouse_name')
        context['relations'] = relations
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


class RelationDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        relation = get_object_or_404(Relation.active_objects, pk=pk)

        if relation.has_related_records():
            messages.error(
                request,
                '発注または問い合わせに紐づく連携情報は削除できません。'
            )
            return redirect(request.POST.get('next') or reverse('relation_list'))

        relation.soft_delete()
        messages.success(request, '連携情報を削除しました。')
        return redirect(request.POST.get('next') or reverse('relation_list'))

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
        try:
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

            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response.write('\ufeff')  # BOMの書き込み
            filename = "一括商品発注表.csv"
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"

            writer = csv.writer(response)
            writer.writerow(['倉庫ID', '倉庫名', 'カテゴリ', '商品ID', '商品名', '現在の在庫数', '発注数'])

            for stock in stocks:
                writer.writerow([
                    stock.warehouse.id,
                    stock.warehouse.warehouse_name,
                    stock.goods.goods_category.category_name,
                    stock.goods.id,
                    stock.goods.goods_name,
                    stock.stock,
                    ''
                ])

            return response

        except Exception as e:
            logger.error("CSV一括発注ダウンロードに失敗しました: %s", e)
            messages.error(request, 'CSVの生成に失敗しました。')
            return redirect('order_goods_list')

class OrderCsvImportView(ShopStaffRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'CSVファイルが選択されていません。')
            return redirect('order_goods_list')

        try:
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file)

            valid_rows = []
            stock_errors = []

            # ─── フェーズ1: バリデーション（全行チェック、DBへの書き込みなし） ───
            for row in reader:
                warehouse_id = row['倉庫ID'].strip()
                goods_id = row['商品ID'].strip()
                order_quantity_str = row['発注数'].strip()
                if not order_quantity_str:
                    continue
                order_quantity = int(order_quantity_str)
                if order_quantity <= 0:
                    continue

                warehouse = Warehouse.active_objects.filter(id=warehouse_id).first()
                goods = Goods.active_objects.filter(id=goods_id).first()

                if not (warehouse and goods):
                    continue

                relation = Relation.active_objects.filter(
                    shop=request.user.shop,
                    warehouse=warehouse
                ).first()
                if not relation:
                    continue

                # 倉庫在庫数チェック
                warehouse_stock = WarehouseStock.active_objects.filter(
                    warehouse=warehouse, goods=goods
                ).first()
                stock = warehouse_stock.stock if warehouse_stock else 0
                if order_quantity > stock:
                    stock_errors.append(
                        f'「{goods.goods_name}」（{warehouse.warehouse_name}）: '
                        f'在庫数 {stock} に対して発注数 {order_quantity} は超過しています。'
                    )
                    continue

                valid_rows.append({
                    'relation': relation,
                    'goods': goods,
                    'quantity': order_quantity,
                })

            # 在庫超過エラーがあれば全件中断
            if stock_errors:
                for error_msg in stock_errors:
                    messages.error(request, error_msg)
                messages.error(request, '在庫数を超える発注があるため、全ての発注をキャンセルしました。CSVを修正して再度アップロードしてください。')
                return redirect('order_goods_list')

            # ─── フェーズ2: 発注作成（バリデーション通過後のみ） ───
            orders = {}
            for item in valid_rows:
                relation = item['relation']
                # 同一倉庫のOrderがすでに存在する場合は新たにOrderを作成せず、既存のOrderにOrderGoodsを追加する
                if relation.id not in orders:
                    orders[relation.id] = Order.objects.create(relation=relation)
                OrderGoods.objects.create(
                    order=orders[relation.id],
                    goods=item['goods'],
                    quantity=item['quantity'],
                )

            messages.success(request, 'CSVファイルから発注を作成しました。')
        except Exception as e:
            messages.error(request, f'CSVファイルの処理中にエラーが発生しました: {str(e)}')
            traceback.print_exc()

        return redirect('order_goods_list')

class OrderHistoryView(ShopStaffRequiredMixin, TemplateView):
    template_name = 'inventory/order_history.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = services.get_order_history_data(self.request.user.shop)

        date_from       = self.request.GET.get('date_from', '')
        date_to         = self.request.GET.get('date_to',   '')
        selected_status = self.request.GET.get('status',    '')

        orders = services.order_filter_by_date_and_status(orders, date_from, date_to, selected_status)

        context['rows']            = services.build_rows(orders)
        context['status_choices']  = Order.Status.choices
        context['date_from']       = date_from
        context['date_to']         = date_to
        context['selected_status'] = selected_status
        return context

# 受注一覧を CSV でダウンロードする。
class OrderHistoryCSVExportView(ShopStaffRequiredMixin, View):

    def get(self, request):
        try:
            orders = services.get_order_history_data(request.user.shop)
            date_from       = self.request.GET.get('date_from', '')
            date_to         = self.request.GET.get('date_to',   '')
            selected_status = self.request.GET.get('status',    '')
            orders = services.order_filter_by_date_and_status(orders, date_from, date_to, selected_status)
            rows   = services.build_rows(orders)

            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response.write('﻿')  # BOM の書き込み（Excel での文字化け防止）
            filename = "発注履歴.csv"
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"

            writer = csv.writer(response)
            writer.writerow(['発注先倉庫', '商品名', '発注個数', 'ステータス', '発注日時', '更新日時'])

            for row in rows:
                order = row['order']
                og    = row['order_goods']
                writer.writerow([
                    order.relation.warehouse.warehouse_name,
                    og.goods.goods_name if og else '',
                    og.quantity         if og else '',
                    order.get_status_display(),
                    order.ordered_at.strftime('%Y-%m-%d %H:%M:%S'),
                    order.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                ])

            return response

        except Exception as e:
            logger.error("発注履歴CSVエクスポートに失敗しました: %s", e)
            messages.error(request, 'CSVの生成に失敗しました。')
            return redirect('order_history')


#発注履歴を PDF でダウンロードする。
class OrderHistoryPDFExportView(ShopStaffRequiredMixin, View):

    def get(self, request):
        import importlib.util
        if importlib.util.find_spec('reportlab') is None:
            logger.error("reportlabがインストールされていません")
            messages.error(request, 'PDF生成に必要なライブラリがインストールされていません。')
            return redirect('order_history')

        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont

        try:
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
            FONT = 'HeiseiKakuGo-W5'

            orders = services.get_order_history_data(request.user.shop)
            date_from       = self.request.GET.get('date_from', '')
            date_to         = self.request.GET.get('date_to',   '')
            selected_status = self.request.GET.get('status',    '')
            orders = services.order_filter_by_date_and_status(orders, date_from, date_to, selected_status)
            rows   = services.build_rows(orders)

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=landscape(A4),
                leftMargin=20, rightMargin=20,
                topMargin=20, bottomMargin=20,
            )

            styles     = getSampleStyleSheet()
            jp_style   = ParagraphStyle('jp',    parent=styles['Normal'],  fontName=FONT, fontSize=9)
            title_style = ParagraphStyle('title', parent=styles['Heading1'], fontName=FONT, fontSize=14)

            elements = []
            elements.append(Paragraph('発注履歴一覧', title_style))
            elements.append(Spacer(1, 12))

            header = ['発注先倉庫', '商品名', '発注個数', 'ステータス', '発注日時', '更新日時']
            table_data = [[Paragraph(h, jp_style) for h in header]]

            for row in rows:
                order = row['order']
                og    = row['order_goods']
                table_data.append([
                    Paragraph(order.relation.warehouse.warehouse_name, jp_style),
                    Paragraph(og.goods.goods_name if og else '',       jp_style),
                    Paragraph(str(og.quantity)    if og else '',       jp_style),
                    Paragraph(order.get_status_display(),              jp_style),
                    Paragraph(order.ordered_at.strftime('%Y-%m-%d %H:%M'), jp_style),
                    Paragraph(order.updated_at.strftime('%Y-%m-%d %H:%M'), jp_style),
                ])

            col_widths = [110, 140, 60, 80, 110, 110]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND',     (0, 0), (-1, 0),  colors.HexColor('#4caf50')),
                ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
                ('FONTNAME',       (0, 0), (-1, -1), FONT),
                ('FONTSIZE',       (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f8e9')]),
                ('GRID',           (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',     (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)

            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = "発注履歴.pdf"
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
            return response

        except Exception as e:
            logger.error("発注履歴PDFエクスポートに失敗しました: %s", e)
            messages.error(request, 'PDFの生成に失敗しました。')
            return redirect('order_history')

def _get_filtered_orders(request):
    """ログイン倉庫の受注クエリセットを返す（フィルタ適用済み）。CSV・PDFビューと共用。"""
    qs = (
        Order.active_objects
        .filter(relation__warehouse=request.user.warehouse)
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

    date_from = request.GET.get('date_from', '').strip()
    date_to   = request.GET.get('date_to',   '').strip()
    status    = request.GET.get('status',    '').strip()

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


_STATUS_TRANSITIONS = {
    Order.Status.ORDERED:   [Order.Status.ORDERED,   Order.Status.PREPARING, Order.Status.CANCELED],
    Order.Status.PREPARING: [Order.Status.PREPARING, Order.Status.SHIPPED,   Order.Status.CANCELED],
    Order.Status.SHIPPED:   [Order.Status.SHIPPED,   Order.Status.DELIVERED, Order.Status.CANCELED],
    Order.Status.DELIVERED: [Order.Status.DELIVERED, Order.Status.CANCELED],
    Order.Status.CANCELED:  [Order.Status.CANCELED],
}


def _build_rows(orders):
    """テンプレート・CSV・PDF 共通のフラット行リストを生成する（rowspan 計算込み）。"""
    rows = []
    for order in orders:
        goods_list = order.active_order_goods
        count = len(goods_list)
        available_statuses = _STATUS_TRANSITIONS.get(order.status, [])
        if count == 0:
            rows.append({'order': order, 'order_goods': None, 'is_first': True, 'goods_count': 1, 'available_statuses': available_statuses})
        else:
            for i, og in enumerate(goods_list):
                rows.append({'order': order, 'order_goods': og, 'is_first': i == 0, 'goods_count': count, 'available_statuses': available_statuses})
    return rows


class WarehouseOrderListView(WarehouseStaffRequiredMixin, TemplateView):
    template_name = 'inventory/warehouse_order_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = _get_filtered_orders(self.request)
        context['rows']            = _build_rows(orders)
        context['status_choices']  = Order.Status.choices
        context['selected_status'] = self.request.GET.get('status',    '')
        context['date_from']       = self.request.GET.get('date_from', '')
        context['date_to']         = self.request.GET.get('date_to',   '')
        return context


class WarehouseOrderStatusUpdateView(WarehouseStaffRequiredMixin, View):

    ALLOWED_STATUSES = {Order.Status.ORDERED.value,
                        Order.Status.PREPARING.value,
                        Order.Status.SHIPPED.value,
                        Order.Status.DELIVERED.value,
                        Order.Status.CANCELED.value,}

    STOCK_DEDUCTED_STATUSES = {
        Order.Status.SHIPPED.value,
        Order.Status.DELIVERED.value,
    }

    def post(self, request, pk):
        with transaction.atomic():
            order = get_object_or_404(
                Order.active_objects.select_for_update(),
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

            old_status = order.status

            # 在庫未減算の状態から発送済みになる時だけ引く
            if (
                old_status not in self.STOCK_DEDUCTED_STATUSES
                and new_status_int == Order.Status.SHIPPED.value
            ):
                minus_stock(order)

            # 在庫減算済みの状態からキャンセルになる時は倉庫在庫を戻す
            if (
                old_status in self.STOCK_DEDUCTED_STATUSES
                and new_status_int == Order.Status.CANCELED.value
            ):
                restore_stock(order)

            # 発送済みから納品済みになる時に店舗在庫を追加する
            if (
                old_status == Order.Status.SHIPPED.value
                and new_status_int == Order.Status.DELIVERED.value
            ):
                add_shop_stock(order)

            # 納品済みからキャンセルになる時に店舗在庫を引く
            if (
                old_status == Order.Status.DELIVERED.value
                and new_status_int == Order.Status.CANCELED.value
            ):
                subtract_shop_stock(order)

            order.status = new_status_int
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'ステータスを更新しました。')
            return redirect(request.POST.get('next') or reverse('warehouse_order_list'))


class WarehouseOrderCSVExportView(WarehouseStaffRequiredMixin, View):
    """受注一覧を CSV でダウンロードする。"""

    def get(self, request):
        try:
            orders = _get_filtered_orders(request)
            rows   = _build_rows(orders)

            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            filename = '受注履歴.csv'
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"

            writer = csv.writer(response)
            writer.writerow(['発注元店舗', '商品名', '発注個数', 'ステータス', '発注日時', '更新日時'])

            for row in rows:
                order = row['order']
                og    = row['order_goods']
                writer.writerow([
                    order.relation.shop.shop_name,
                    og.goods.goods_name if og else '',
                    og.quantity         if og else '',
                    order.get_status_display(),
                    order.ordered_at.strftime('%Y-%m-%d %H:%M:%S'),
                    order.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                ])

            return response

        except Exception as e:
            logger.error("受注CSVエクスポートに失敗しました: %s", e)
            messages.error(request, 'CSVの生成に失敗しました。')
            return redirect('warehouse_order_list')


class WarehouseOrderPDFExportView(WarehouseStaffRequiredMixin, View):
    """受注一覧を PDF でダウンロードする。"""

    def get(self, request):
        import importlib.util
        if importlib.util.find_spec('reportlab') is None:
            logger.error("reportlabがインストールされていません")
            messages.error(request, 'PDF生成に必要なライブラリがインストールされていません。')
            return redirect('warehouse_order_list')

        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont

        try:
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
            FONT = 'HeiseiKakuGo-W5'

            orders = _get_filtered_orders(request)
            rows   = _build_rows(orders)

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=landscape(A4),
                leftMargin=20, rightMargin=20,
                topMargin=20, bottomMargin=20,
            )

            styles     = getSampleStyleSheet()
            jp_style   = ParagraphStyle('jp',    parent=styles['Normal'],  fontName=FONT, fontSize=9)
            title_style = ParagraphStyle('title', parent=styles['Heading1'], fontName=FONT, fontSize=14)

            elements = []
            elements.append(Paragraph('受注管理一覧', title_style))
            elements.append(Spacer(1, 12))

            header = ['発注元店舗', '商品名', '発注個数', 'ステータス', '発注日時', '更新日時']
            table_data = [[Paragraph(h, jp_style) for h in header]]

            for row in rows:
                order = row['order']
                og    = row['order_goods']
                table_data.append([
                    Paragraph(order.relation.shop.shop_name,          jp_style),
                    Paragraph(og.goods.goods_name if og else '',       jp_style),
                    Paragraph(str(og.quantity)    if og else '',       jp_style),
                    Paragraph(order.get_status_display(),              jp_style),
                    Paragraph(order.ordered_at.strftime('%Y-%m-%d %H:%M'), jp_style),
                    Paragraph(order.updated_at.strftime('%Y-%m-%d %H:%M'), jp_style),
                ])

            col_widths = [110, 140, 60, 80, 110, 110]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND',     (0, 0), (-1, 0),  colors.HexColor('#4caf50')),
                ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
                ('FONTNAME',       (0, 0), (-1, -1), FONT),
                ('FONTSIZE',       (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f8e9')]),
                ('GRID',           (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',     (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)

            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = '受注履歴.pdf'
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
            return response

        except Exception as e:
            logger.error("受注PDFエクスポートに失敗しました: %s", e)
            messages.error(request, 'PDFの生成に失敗しました。')
            return redirect('warehouse_order_list')
    
    
