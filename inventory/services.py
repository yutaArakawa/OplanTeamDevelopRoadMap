from django.db.models import Prefetch
from inventory.models import Goods, GoodsCategory, Relation, Warehouse, Shop, WarehouseStock, Order, OrderGoods

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