import pytest
from django.urls import reverse
from django.core.management import call_command
from datetime import datetime
from inventory.models import Order, OrderGoods
from dashboard.models import MonthlyOrderSummary

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# ダッシュボード
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('home'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_get_200(self, client, admin_user):
        """管理者はダッシュボードを表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def test_admin_context_has_summary_counts(self, client, admin_user, shop, warehouse, goods, goods_category):
        """管理者ダッシュボードには各種カウントが含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('home'))
        ctx = response.context
        assert 'warehouse_count' in ctx
        assert 'shop_count' in ctx
        assert 'goods_count' in ctx
        assert 'category_count' in ctx
        assert 'user_count' in ctx
        assert 'pending_order_count' in ctx

    def test_admin_pending_order_count(self, client, admin_user, relation, goods):
        """管理者ダッシュボードの pending_order_count が発注済みの件数を反映する"""
        order = Order.objects.create(relation=relation, status=Order.Status.ORDERED)
        OrderGoods.objects.create(order=order, goods=goods, quantity=1)
        client.force_login(admin_user)
        response = client.get(reverse('home'))
        assert response.context['pending_order_count'] >= 1

    def test_shop_user_get_200(self, client, shop_user):
        """店舗スタッフはダッシュボードを表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def test_shop_user_context_has_rankings(self, client, shop_user):
        """店舗スタッフダッシュボードにはランキングが含まれる"""
        client.force_login(shop_user)
        response = client.get(reverse('home'))
        ctx = response.context
        assert 'shop_ranking' in ctx
        assert 'all_shop_ranking' in ctx

    def test_shop_ranking_includes_recent_orders(self, client, shop_user, relation, goods):
        """店舗スタッフのランキングに直近の発注が反映される"""
        order = Order.objects.create(relation=relation)
        OrderGoods.objects.create(order=order, goods=goods, quantity=10)
        client.force_login(shop_user)
        response = client.get(reverse('home'))
        ranking_names = [r['goods__goods_name'] for r in response.context['shop_ranking']]
        assert goods.goods_name in ranking_names

    def test_warehouse_user_get_200(self, client, warehouse_user):
        """倉庫スタッフはダッシュボードを表示できる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def test_warehouse_user_context_has_stock_info(self, client, warehouse_user):
        """倉庫スタッフダッシュボードには在庫情報が含まれる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('home'))
        ctx = response.context
        assert 'warehouse_stocks' in ctx
        assert 'stock_count' in ctx
        assert 'new_order_count' in ctx
        assert 'preparing_order_count' in ctx

    def test_warehouse_new_order_count(self, client, warehouse_user, relation, goods):
        """倉庫スタッフダッシュボードの new_order_count が発注済み受注件数を反映する"""
        order = Order.objects.create(relation=relation, status=Order.Status.ORDERED)
        OrderGoods.objects.create(order=order, goods=goods, quantity=2)
        client.force_login(warehouse_user)
        response = client.get(reverse('home'))
        assert response.context['new_order_count'] >= 1

    def test_warehouse_preparing_order_count(self, client, warehouse_user, relation, goods):
        """倉庫スタッフダッシュボードの preparing_order_count が準備中受注件数を反映する"""
        order = Order.objects.create(relation=relation, status=Order.Status.PREPARING)
        OrderGoods.objects.create(order=order, goods=goods, quantity=3)
        client.force_login(warehouse_user)
        response = client.get(reverse('home'))
        assert response.context['preparing_order_count'] >= 1


# ---------------------------------------------------------------------------
# 月次注文サマリー更新バッチ
# ---------------------------------------------------------------------------

class TestUpdateMonthlyOrderSummary:
    """update_monthly_order_summary management command のテスト"""

    def test_command_executes_successfully(self):
        """コマンドが正常に実行される"""
        try:
            call_command('update_monthly_order_summary')
        except Exception as e:
            pytest.fail(f"コマンド実行に失敗しました: {e}")

    def test_creates_monthly_summary_records(self, shop, relation, goods):
        """月次サマリーレコードが作成される"""
        # テストデータ作成
        order = Order.objects.create(relation=relation, status=Order.Status.ORDERED)
        OrderGoods.objects.create(order=order, goods=goods, quantity=5)

        # コマンド実行前の件数
        count_before = MonthlyOrderSummary.objects.filter(
            count_date=datetime.now().date()
        ).count()

        # コマンド実行
        call_command('update_monthly_order_summary')

        # コマンド実行後の件数
        count_after = MonthlyOrderSummary.objects.filter(
            count_date=datetime.now().date()
        ).count()

        assert count_after > count_before

    def test_no_duplicate_records_on_multiple_executions(self, shop, relation, goods):
        """複数回実行しても重複レコードが作成されない"""
        # テストデータ作成
        order = Order.objects.create(relation=relation, status=Order.Status.ORDERED)
        OrderGoods.objects.create(order=order, goods=goods, quantity=5)

        count_date = datetime.now().date()

        # 1回目の実行
        call_command('update_monthly_order_summary')
        count_first = MonthlyOrderSummary.objects.filter(count_date=count_date).count()

        # 2回目の実行
        call_command('update_monthly_order_summary')
        count_second = MonthlyOrderSummary.objects.filter(count_date=count_date).count()

        # 1回目と2回目の件数が同じ（重複が削除されている）
        assert count_first == count_second

    def test_summary_data_accuracy(self, shop, relation, goods):
        """月次サマリーが正確な注文数を反映している"""
        # 複数の注文を作成
        for i in range(3):
            order = Order.objects.create(relation=relation, status=Order.Status.ORDERED)
            OrderGoods.objects.create(order=order, goods=goods, quantity=10 + i)

        # コマンド実行
        call_command('update_monthly_order_summary')

        # 本日のサマリーを取得
        count_date = datetime.now().date()
        summaries = MonthlyOrderSummary.objects.filter(count_date=count_date)

        # レコードが存在することを確認
        assert summaries.exists()

        # 発注数が 0 より大きいことを確認
        total_quantity = sum(s.total_quantity for s in summaries)
        assert total_quantity > 0
