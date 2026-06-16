from dashboard.models import MonthlyOrderSummary
from django.db.models import Sum

# 対象日に作成された店舗毎(店舗指定がない場合は全店舗)の月の発注数を取得
def get_monthly_order_summary(date, shop=None):
    qs = MonthlyOrderSummary.active_objects.filter(
        count_date=date
    )
    if shop:
        qs = qs.filter(shop=shop)
    
    return qs.select_related('goods')

# 最新の集計日付を返す。データがなければ None を返す
def get_latest_summary_date():
    latest = MonthlyOrderSummary.active_objects.order_by('-count_date').values('count_date').first()

    return latest['count_date'] if latest else None

# 月次の発注数ランキングを取得
def get_order_ranking(summary_queryset, limit=10):
    return summary_queryset.values(
        'goods__goods_name',
        'goods_id'
    ).annotate(
        total_quantity_sum=Sum('total_quantity')
    ).order_by('-total_quantity_sum')[:limit]
