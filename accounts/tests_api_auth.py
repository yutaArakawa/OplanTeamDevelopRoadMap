import json
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestCsrfAPIView:
    def test_get_returns_csrf_token(self, client):
        response = client.get(reverse('api_csrf'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'csrfToken' in data
        assert data['csrfToken']


class TestLoginAPIView:
    def test_login_success(self, client, admin_user):
        response = client.post(
            reverse('api_login'),
            data=json.dumps({'username': 'admin_user', 'password': 'testpass123'}),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.content)['status'] == 'ok'

    def test_login_wrong_password(self, client, admin_user):
        response = client.post(
            reverse('api_login'),
            data=json.dumps({'username': 'admin_user', 'password': 'wrong'}),
            content_type='application/json',
        )
        assert response.status_code == 401

    def test_login_unknown_user(self, client):
        response = client.post(
            reverse('api_login'),
            data=json.dumps({'username': 'nobody', 'password': 'testpass123'}),
            content_type='application/json',
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        response = client.post(
            reverse('api_login'),
            data=json.dumps({'username': '', 'password': ''}),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_login_deleted_user(self, client, deleted_user):
        response = client.post(
            reverse('api_login'),
            data=json.dumps({'username': 'deleted_user', 'password': 'testpass123'}),
            content_type='application/json',
        )
        assert response.status_code == 401


class TestLogoutAPIView:
    def test_logout_success(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post(
            reverse('api_logout'),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.content)['status'] == 'ok'


class TestMeAPIView:
    def test_me_authenticated(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse('api_me'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['username'] == 'admin_user'
        assert data['authority'] == admin_user.authority_id

    def test_me_unauthenticated(self, client):
        response = client.get(reverse('api_me'))
        assert response.status_code == 401

    def test_me_shop_user_includes_shop(self, client, shop_user):
        client.force_login(shop_user)
        response = client.get(reverse('api_me'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['shop'] == shop_user.shop.shop_name

    def test_me_warehouse_user_includes_warehouse(self, client, warehouse_user):
        client.force_login(warehouse_user)
        response = client.get(reverse('api_me'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['warehouse'] == warehouse_user.warehouse.warehouse_name
