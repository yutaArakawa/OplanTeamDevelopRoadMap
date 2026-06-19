import json
import pytest
from django.urls import reverse
from accounts.models import User

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# ユーザー一覧 API
# ---------------------------------------------------------------------------

class TestUserListAPIView:
    def test_unauthenticated_returns_401(self, client):
        response = client.get(reverse('api_user_list'))
        assert response.status_code == 401

    def test_admin_gets_all_users(self, client, admin_user, shop_user, warehouse_user):
        client.force_login(admin_user)
        response = client.get(reverse('api_user_list'))
        assert response.status_code == 200
        data = json.loads(response.content)
        usernames = [u['username'] for u in data['users']]
        assert 'shop_user' in usernames
        assert 'warehouse_user' in usernames

    def test_admin_gets_filter_options(self, client, admin_user, authority_shop, shop, warehouse):
        client.force_login(admin_user)
        response = client.get(reverse('api_user_list'))
        data = json.loads(response.content)
        assert len(data['authorities']) > 0
        assert len(data['shops']) > 0
        assert len(data['warehouses']) > 0

    def test_shop_user_sees_only_own_shop_users(self, client, shop_user, admin_user):
        client.force_login(shop_user)
        response = client.get(reverse('api_user_list'))
        assert response.status_code == 200
        data = json.loads(response.content)
        # 店舗スタッフは同じ店舗のユーザーのみ表示
        for u in data['users']:
            assert u['authority_id'] == shop_user.authority_id

    def test_shop_user_gets_no_filter_options(self, client, shop_user):
        client.force_login(shop_user)
        response = client.get(reverse('api_user_list'))
        data = json.loads(response.content)
        assert data['authorities'] == []
        assert data['shops'] == []
        assert data['warehouses'] == []

    def test_filter_by_authority(self, client, admin_user, shop_user, warehouse_user):
        client.force_login(admin_user)
        response = client.get(
            reverse('api_user_list'),
            {'authority': shop_user.authority_id},
        )
        data = json.loads(response.content)
        for u in data['users']:
            assert u['authority_id'] == shop_user.authority_id

    def test_filter_by_shop(self, client, admin_user, shop_user):
        client.force_login(admin_user)
        response = client.get(
            reverse('api_user_list'),
            {'shop': shop_user.shop_id},
        )
        data = json.loads(response.content)
        usernames = [u['username'] for u in data['users']]
        assert 'shop_user' in usernames

    def test_deleted_user_not_listed(self, client, admin_user, deleted_user):
        client.force_login(admin_user)
        response = client.get(reverse('api_user_list'))
        data = json.loads(response.content)
        usernames = [u['username'] for u in data['users']]
        assert 'deleted_user' not in usernames


# ---------------------------------------------------------------------------
# ユーザー作成 API
# ---------------------------------------------------------------------------

class TestUserCreateAPIView:
    def test_get_returns_form_options(self, client, admin_user, authority_shop, shop, warehouse):
        client.force_login(admin_user)
        response = client.get(reverse('api_user_create'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'authorities' in data
        assert 'shops' in data
        assert 'warehouses' in data

    def test_unauthenticated_post_returns_401(self, client):
        response = client.post(
            reverse('api_user_create'),
            data=json.dumps({}),
            content_type='application/json',
        )
        assert response.status_code == 401

    def test_non_admin_post_returns_403(self, client, shop_user):
        client.force_login(shop_user)
        response = client.post(
            reverse('api_user_create'),
            data=json.dumps({}),
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_admin_can_create_user(self, client, admin_user, authority_shop, shop):
        client.force_login(admin_user)
        response = client.post(
            reverse('api_user_create'),
            data=json.dumps({
                'username': 'new_shop_user',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'user_gender': '2',
                'authority': str(authority_shop.id),
                'shop': str(shop.id),
                'warehouse': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert User.objects.filter(username='new_shop_user').exists()

    def test_create_fails_on_missing_username(self, client, admin_user, authority_shop, shop):
        client.force_login(admin_user)
        response = client.post(
            reverse('api_user_create'),
            data=json.dumps({
                'username': '',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'user_gender': '1',
                'authority': str(authority_shop.id),
                'shop': str(shop.id),
                'warehouse': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'username' in json.loads(response.content)['errors']

    def test_create_fails_on_duplicate_username(self, client, admin_user, shop_user, authority_shop, shop):
        client.force_login(admin_user)
        response = client.post(
            reverse('api_user_create'),
            data=json.dumps({
                'username': 'shop_user',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'user_gender': '1',
                'authority': str(authority_shop.id),
                'shop': str(shop.id),
                'warehouse': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'username' in json.loads(response.content)['errors']

    def test_create_fails_on_missing_gender(self, client, admin_user, authority_shop, shop):
        client.force_login(admin_user)
        response = client.post(
            reverse('api_user_create'),
            data=json.dumps({
                'username': 'new_user',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'user_gender': '',
                'authority': str(authority_shop.id),
                'shop': str(shop.id),
                'warehouse': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'user_gender' in json.loads(response.content)['errors']

    def test_create_fails_on_password_mismatch(self, client, admin_user, authority_shop, shop):
        client.force_login(admin_user)
        response = client.post(
            reverse('api_user_create'),
            data=json.dumps({
                'username': 'new_user',
                'password1': 'testpass123',
                'password2': 'different',
                'user_gender': '1',
                'authority': str(authority_shop.id),
                'shop': str(shop.id),
                'warehouse': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'password2' in json.loads(response.content)['errors']

    def test_create_shop_user_without_shop_fails(self, client, admin_user, authority_shop):
        client.force_login(admin_user)
        response = client.post(
            reverse('api_user_create'),
            data=json.dumps({
                'username': 'new_user',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'user_gender': '1',
                'authority': str(authority_shop.id),
                'shop': '',
                'warehouse': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'shop' in json.loads(response.content)['errors']


# ---------------------------------------------------------------------------
# ユーザー詳細 / 更新 / 削除 API
# ---------------------------------------------------------------------------

class TestUserDetailAPIView:
    def test_get_returns_user_data(self, client, admin_user, shop_user):
        client.force_login(admin_user)
        response = client.get(reverse('api_user_detail', kwargs={'pk': shop_user.pk}))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['user']['username'] == 'shop_user'

    def test_get_nonexistent_user_returns_404(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse('api_user_detail', kwargs={'pk': 99999}))
        assert response.status_code == 404

    def test_get_unauthenticated_returns_401(self, client, shop_user):
        response = client.get(reverse('api_user_detail', kwargs={'pk': shop_user.pk}))
        assert response.status_code == 401

    # ---- 更新 ----

    def test_admin_can_update_all_fields(self, client, admin_user, shop_user, authority_shop):
        client.force_login(admin_user)
        response = client.put(
            reverse('api_user_detail', kwargs={'pk': shop_user.pk}),
            data=json.dumps({
                'username': 'updated_user',
                'user_gender': '2',
                'authority': str(authority_shop.id),
                'shop': str(shop_user.shop_id),
                'warehouse': '',
                'new_password1': '',
                'new_password2': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        shop_user.refresh_from_db()
        assert shop_user.username == 'updated_user'
        assert shop_user.user_gender == 2

    def test_admin_can_change_password(self, client, admin_user, shop_user, authority_shop):
        client.force_login(admin_user)
        client.put(
            reverse('api_user_detail', kwargs={'pk': shop_user.pk}),
            data=json.dumps({
                'username': shop_user.username,
                'user_gender': str(shop_user.user_gender),
                'authority': str(shop_user.authority_id),
                'shop': str(shop_user.shop_id),
                'warehouse': '',
                'new_password1': 'newpass123',
                'new_password2': 'newpass123',
            }),
            content_type='application/json',
        )
        shop_user.refresh_from_db()
        assert shop_user.check_password('newpass123')

    def test_update_fails_on_duplicate_username(self, client, admin_user, shop_user, warehouse_user, authority_shop):
        client.force_login(admin_user)
        response = client.put(
            reverse('api_user_detail', kwargs={'pk': shop_user.pk}),
            data=json.dumps({
                'username': 'warehouse_user',
                'user_gender': '1',
                'authority': str(authority_shop.id),
                'shop': str(shop_user.shop_id),
                'warehouse': '',
                'new_password1': '',
                'new_password2': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'username' in json.loads(response.content)['errors']

    def test_shop_staff_can_only_update_shop(self, client, shop_user, shop2):
        client.force_login(shop_user)
        response = client.put(
            reverse('api_user_detail', kwargs={'pk': shop_user.pk}),
            data=json.dumps({
                'shop': str(shop2.id),
                'warehouse': '',
                'new_password1': '',
                'new_password2': '',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        shop_user.refresh_from_db()
        assert shop_user.shop_id == shop2.id

    # ---- 削除 ----

    def test_admin_can_delete_user(self, client, admin_user, shop_user):
        client.force_login(admin_user)
        response = client.delete(reverse('api_user_detail', kwargs={'pk': shop_user.pk}))
        assert response.status_code == 200
        shop_user.refresh_from_db()
        assert shop_user.delete_flg is True

    def test_non_admin_cannot_delete(self, client, shop_user):
        client.force_login(shop_user)
        response = client.delete(reverse('api_user_detail', kwargs={'pk': shop_user.pk}))
        assert response.status_code == 403

    def test_cannot_delete_self(self, client, admin_user):
        client.force_login(admin_user)
        response = client.delete(reverse('api_user_detail', kwargs={'pk': admin_user.pk}))
        assert response.status_code == 400

    def test_delete_nonexistent_user_returns_404(self, client, admin_user):
        client.force_login(admin_user)
        response = client.delete(reverse('api_user_detail', kwargs={'pk': 99999}))
        assert response.status_code == 404
