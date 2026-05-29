import pytest
from django.urls import reverse
from inventory.models import Order, OrderGoods

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
