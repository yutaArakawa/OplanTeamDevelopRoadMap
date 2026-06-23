import pytest
from django.urls import reverse


class TestShopNameAutocomplete:
    url = reverse('shop_name_autocomplete')

    def test_partial_match_returns_results(self, client, admin_user, shop):
        """部分一致で候補が返ること"""
        client.force_login(admin_user)
        response = client.get(self.url, {'q': 'テスト'})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == shop.shop_name
        assert data[0]['id'] == shop.id

    def test_empty_query_returns_all(self, client, admin_user, shop, shop2):
        """空文字で全件返ること"""
        client.force_login(admin_user)
        response = client.get(self.url, {'q': ''})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_no_match_returns_empty(self, client, admin_user, shop):
        """一致しない場合は空リストが返ること"""
        client.force_login(admin_user)
        response = client.get(self.url, {'q': '存在しない店舗'})
        assert response.status_code == 200
        assert response.json() == []

    def test_deleted_shop_not_returned(self, client, admin_user, shop):
        """削除済み店舗は返らないこと"""
        shop.delete_flg = True
        shop.save()
        client.force_login(admin_user)
        response = client.get(self.url, {'q': 'テスト'})
        assert response.status_code == 200
        assert response.json() == []

    def test_response_contains_id_and_name(self, client, admin_user, shop):
        """レスポンスに id と name が含まれること"""
        client.force_login(admin_user)
        response = client.get(self.url, {'q': 'テスト'})
        data = response.json()
        assert 'id' in data[0]
        assert 'name' in data[0]


class TestWarehouseNameAutocomplete:
    url = reverse('warehouse_name_autocomplete')

    def test_partial_match_returns_results(self, client, admin_user, warehouse):
        """部分一致で候補が返ること"""
        client.force_login(admin_user)
        response = client.get(self.url, {'q': 'テスト'})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == warehouse.warehouse_name
        assert data[0]['id'] == warehouse.id

    def test_empty_query_returns_all(self, client, admin_user, warehouse, warehouse2):
        """空文字で全件返ること"""
        client.force_login(admin_user)
        response = client.get(self.url, {'q': ''})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_no_match_returns_empty(self, client, admin_user, warehouse):
        """一致しない場合は空リストが返ること"""
        client.force_login(admin_user)
        response = client.get(self.url, {'q': '存在しない倉庫'})
        assert response.status_code == 200
        assert response.json() == []

    def test_deleted_warehouse_not_returned(self, client, admin_user, warehouse):
        """削除済み倉庫は返らないこと"""
        warehouse.delete_flg = True
        warehouse.save()
        client.force_login(admin_user)
        response = client.get(self.url, {'q': 'テスト'})
        assert response.status_code == 200
        assert response.json() == []

    def test_response_contains_id_and_name(self, client, admin_user, warehouse):
        """レスポンスに id と name が含まれること"""
        client.force_login(admin_user)
        response = client.get(self.url, {'q': 'テスト'})
        data = response.json()
        assert 'id' in data[0]
        assert 'name' in data[0]
