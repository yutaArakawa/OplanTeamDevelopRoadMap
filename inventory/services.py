from django.db.models import Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from inventory.models import Order, OrderGoods, Goods, GoodsCategory, ShopStock, WarehouseStock

# 店舗の注文履歴データを取得するサービス関数
def get_order_history_data(shop):
    orders = Order.active_objects.filter(
        relation__shop=shop
    ).select_related(
        'relation',
        'relation__warehouse'
    ).prefetch_related(
        Prefetch(
            'ordergoods_set',
            queryset=OrderGoods.active_objects.select_related('goods'),
            to_attr='active_order_goods',
        )
    ).order_by('-created_at')

    return orders

def order_filter_by_date_and_status(qs, date_from, date_to, status):
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

#テンプレート・CSV・PDF 共通のフラット行リストを生成する（rowspan 計算込み）。
def build_rows(orders):
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

# 商品IDから商品データを取得するサービス関数
def get_goods_by_goods_id(goods_id):
    return get_object_or_404(Goods, pk=goods_id)

# 店舗と商品から店舗在庫データを取得するサービス関数
def get_shop_stock_by_goods_and_shop(goods, shop):
    return ShopStock.active_objects.filter(
        goods=goods,
        shop=shop
    ).first()

# 商品カテゴリの選択肢を取得するサービス関数
def get_goods_categories():
    return GoodsCategory.active_objects.all()

# 店舗の商品在庫を取得するサービス関数
def get_shop_stock_list(shop):
    return Goods.active_objects.select_related('goods_category').annotate(
        # レコードがあればそのままstock、なければ0で表示
        stock=Coalesce(
            Sum('shopstock__stock', filter=Q(shopstock__shop=shop, shopstock__delete_flg=False)), 0
        )
    )

# 店舗在庫を更新または作成するサービス関数
def update_or_create_shop_stock(goods, shop, stock_value):
    ShopStock.objects.update_or_create(
        goods=goods,
        shop=shop,
        defaults={'stock': stock_value}
    )

# 商品作成時に、全倉庫の在庫にレコード追加するサービス関数
def insert_initial_warehouse_stock_for_goods(goods, warehouses):
    for warehouse in warehouses:
        WarehouseStock.objects.get_or_create(
            warehouse=warehouse,
            goods=goods,
            defaults={'stock': 0}
        )

# 商品作成時に、全店舗の在庫にレコード追加するサービス関数
def insert_initial_shop_stock_for_goods(goods, shops):
    for shop in shops:
        ShopStock.objects.get_or_create(
            shop=shop,
            goods=goods,
            defaults={'stock': 0}
        )


# 倉庫スタッフユーザーが発送済みを選択した際、在庫数から発送数を引いて処理する関数
def minus_stock(order):

    warehouse = order.relation.warehouse

    order_goods_list = OrderGoods.objects.filter(order=order)

    for order_goods in order_goods_list:

        stock = WarehouseStock.objects.get(
            warehouse=warehouse,
            goods=order_goods.goods
        )

        stock.stock -= order_goods.quantity
        stock.save(update_fields=["stock"])


# 発送済みから準備中に戻した際、在庫数を元に戻す関数
def restore_stock(order):

    warehouse = order.relation.warehouse

    order_goods_list = OrderGoods.objects.filter(order=order)

    for order_goods in order_goods_list:

        stock = WarehouseStock.objects.get(
            warehouse=warehouse,
            goods=order_goods.goods
        )

        stock.stock += order_goods.quantity
        stock.save(update_fields=["stock"])
