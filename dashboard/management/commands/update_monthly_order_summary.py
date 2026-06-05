from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from dashboard.models import MonthlyOrderSummary
from inventory.models import Order, OrderGoods

class Command(BaseCommand):
    help = '店舗別の月次の注文数集計を更新するコマンド'

    def handle(self, *args, **options):

        # 集計対象の期間を設定（例: 1ヶ月前から現在まで）
        # 集計日は現在の日付とする(23時に実行される想定)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        # 指定期間分の店舗別の月次の注文数集計を取得
        orders = get_shops_monthly_order_summary(start_date, end_date)
        # 集計結果をMonthlyOrderSummaryモデルに保存
        save_monthly_order_summary(orders, end_date)

        self.stdout.write(self.style.SUCCESS('月次の注文数集計が更新されました。'))


# 指定期間分の店舗別の月次の注文数集計を取得する関数
def get_shops_monthly_order_summary(start_date, end_date):
        return Order.active_objects.filter(
            ordered_at__date__gte=start_date,
            ordered_at__date__lte=end_date
        ).prefetch_related(
            'relation__shop',
            'ordergoods_set',
        ).values(
            'relation__shop',
            'ordergoods__goods'
        ).annotate(
            total_quantity=Sum('ordergoods__quantity')
        )

# 集計結果をMonthlyOrderSummaryモデルに保存
def save_monthly_order_summary(summary_data, count_date):
     # 当日のレコードをクリア（重複を防ぐ）
     MonthlyOrderSummary.objects.filter(count_date=count_date).delete()

     # 新規作成
     MonthlyOrderSummary.objects.bulk_create([
          MonthlyOrderSummary(
               count_date=count_date,
               shop_id=item['relation__shop'],
               goods_id=item['ordergoods__goods'],
               total_quantity=item['total_quantity']
          )
          for item in summary_data
     ])
