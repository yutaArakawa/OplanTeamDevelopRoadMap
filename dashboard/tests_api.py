import json
import pytest
from django.urls import reverse
from dashboard.models import MonthlyOrderSummary

pytestmark = pytest.mark.django_db


class TestHomeAPIViewAdmin:
    def test_unauthenticated_returns_401(self, client):
        response = client.get(reverse('api_dashboard'))
        assert response.status_code == 401

    def test_admin_gets_summary_data(self, client, admin_user, shop, warehouse):
        client.force_login(admin_user)
        response = client.get(reverse('api_dashboard'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'warehouse_count' in data
        assert 'shop_count' in data
        assert 'goods_count' in data
        assert 'category_count' in data
        assert 'user_count' in data
        assert 'pending_order_count' in data

    def test_admin_counts_are_integers(self, client, admin_user):
        client.force_login(admin_user)
        data = json.loads(client.get(reverse('api_dashboard')).content)
        for key in ('warehouse_count', 'shop_count', 'goods_count',
                    'category_count', 'user_count', 'pending_order_count'):
            assert isinstance(data[key], int)


class TestHomeAPIViewShop:
    def test_shop_user_gets_ranking_data(self, client, shop_user):
        client.force_login(shop_user)
        response = client.get(reverse('api_dashboard'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'shop_ranking' in data
        assert 'all_shop_ranking' in data
        assert 'ranking_date' in data

    def test_shop_ranking_empty_when_no_summary(self, client, shop_user):
        client.force_login(shop_user)
        data = json.loads(client.get(reverse('api_dashboard')).content)
        assert data['shop_ranking'] == []
        assert data['all_shop_ranking'] == []
        assert data['ranking_date'] is None

    def test_shop_ranking_present_when_summary_exists(
        self, client, shop_user, goods, goods_category
    ):
        from django.utils import timezone
        yesterday = timezone.now().date() - __import__('datetime').timedelta(days=1)
        MonthlyOrderSummary.objects.create(
            shop=shop_user.shop,
            goods=goods,
            count_date=yesterday,
            total_quantity=5,
        )
        client.force_login(shop_user)
        data = json.loads(client.get(reverse('api_dashboard')).content)
        assert data['ranking_date'] == str(yesterday)
        assert len(data['shop_ranking']) > 0


class TestHomeAPIViewWarehouse:
    def test_warehouse_user_gets_stock_data(self, client, warehouse_user, warehouse_stock):
        client.force_login(warehouse_user)
        response = client.get(reverse('api_dashboard'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'stock_count' in data
        assert 'new_order_count' in data
        assert 'preparing_order_count' in data
        assert 'warehouse_stocks' in data

    def test_warehouse_stock_count_correct(self, client, warehouse_user, warehouse_stock):
        client.force_login(warehouse_user)
        data = json.loads(client.get(reverse('api_dashboard')).content)
        assert data['stock_count'] == 1

    def test_warehouse_stocks_include_goods_name(self, client, warehouse_user, warehouse_stock):
        client.force_login(warehouse_user)
        data = json.loads(client.get(reverse('api_dashboard')).content)
        assert len(data['warehouse_stocks']) == 1
        assert 'goods__goods_name' in data['warehouse_stocks'][0]
        assert 'stock' in data['warehouse_stocks'][0]
