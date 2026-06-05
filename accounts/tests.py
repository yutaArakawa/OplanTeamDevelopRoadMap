import pytest
from django.core.management import call_command
from django.urls import reverse
from accounts.models import Authority, User

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# ログイン
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_page_returns_200(self, client):
        """ログインページが表示される"""
        response = client.get(reverse('login'))
        assert response.status_code == 200

    def test_login_success(self, client, admin_user):
        """正しいID/PWでログインできる"""
        response = client.post(reverse('login'), {
            'username': 'admin_user',
            'password': 'testpass123',
        })
        assert response.status_code == 302
        assert response.url == '/'

    def test_login_fail_wrong_password(self, client, admin_user):
        """間違ったPWで弾かれる"""
        response = client.post(reverse('login'), {
            'username': 'admin_user',
            'password': 'wrongpassword',
        })
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_login_fail_unknown_user(self, client):
        """存在しないユーザーで弾かれる"""
        response = client.post(reverse('login'), {
            'username': 'nobody',
            'password': 'testpass123',
        })
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated


# ---------------------------------------------------------------------------
# ユーザー一覧 – 編集ボタン
# ---------------------------------------------------------------------------

class TestUserList:
    def test_edit_button_exists(self, client, admin_user, shop_user):
        """ユーザー一覧に編集ボタンが表示される"""
        client.force_login(admin_user)
        response = client.get(reverse('user_list'))
        assert response.status_code == 200
        assert '編集' in response.content.decode()

    def test_edit_button_links_to_user_update(self, client, admin_user, shop_user):
        """編集ボタンが正しい user_update URL を指している"""
        client.force_login(admin_user)
        response = client.get(reverse('user_list'))
        expected_url = reverse('user_update', kwargs={'pk': shop_user.pk})
        assert expected_url in response.content.decode()


# ---------------------------------------------------------------------------
# ユーザー編集画面
# ---------------------------------------------------------------------------

class TestUserUpdate:
    def test_update_page_accessible(self, client, admin_user, shop_user):
        """編集ページに正常アクセスできる"""
        client.force_login(admin_user)
        response = client.get(reverse('user_update', kwargs={'pk': shop_user.pk}))
        assert response.status_code == 200

    def test_update_page_shows_user_info(self, client, admin_user, shop_user):
        """編集ページに対象ユーザーの情報が表示される"""
        client.force_login(admin_user)
        response = client.get(reverse('user_update', kwargs={'pk': shop_user.pk}))
        assert shop_user.username in response.content.decode()

    # ---- 管理者 ----

    def test_admin_all_fields_editable(self, client, admin_user, shop_user):
        """管理者はすべてのフィールドが編集可能（disabled でない）"""
        client.force_login(admin_user)
        response = client.get(reverse('user_update', kwargs={'pk': shop_user.pk}))
        form = response.context['form']
        assert 'username' in form.fields and not form.fields['username'].disabled
        assert 'user_gender' in form.fields and not form.fields['user_gender'].disabled
        assert 'authority' in form.fields and not form.fields['authority'].disabled

    def test_admin_delete_button_visible(self, client, admin_user, shop_user):
        """管理者ログイン時は削除ボタンが表示される"""
        client.force_login(admin_user)
        response = client.get(reverse('user_update', kwargs={'pk': shop_user.pk}))
        # 削除モーダルを開くトリガーボタンが存在する
        assert 'data-bs-target="#deleteModal"' in response.content.decode()

    def test_admin_can_update_user(self, client, admin_user, shop_user):
        """管理者はユーザー情報を正常に更新できる"""
        client.force_login(admin_user)
        url = reverse('user_update', kwargs={'pk': shop_user.pk})
        response = client.post(url, {
            'username': 'updated_shop_user',
            'user_gender': 2,
            'authority': shop_user.authority_id,
            'shop': shop_user.shop_id,
            'new_password1': '',
            'new_password2': '',
        })
        assert response.status_code == 302
        shop_user.refresh_from_db()
        assert shop_user.username == 'updated_shop_user'
        assert shop_user.user_gender == 2

    # ---- 店舗スタッフ ----

    def test_shop_staff_only_shop_field_editable(self, client, shop_user):
        """店舗スタッフは所属店舗のみ編集可能、他フィールドは disabled"""
        client.force_login(shop_user)
        response = client.get(reverse('user_update', kwargs={'pk': shop_user.pk}))
        form = response.context['form']
        assert form.fields['username'].disabled
        assert form.fields['user_gender'].disabled
        assert form.fields['authority'].disabled
        assert 'warehouse' not in form.fields

    def test_shop_staff_no_delete_button(self, client, shop_user):
        """店舗スタッフは削除ボタンが非表示"""
        client.force_login(shop_user)
        response = client.get(reverse('user_update', kwargs={'pk': shop_user.pk}))
        # 削除モーダルを開くトリガーボタンが存在しない
        assert 'data-bs-target="#deleteModal"' not in response.content.decode()

    def test_shop_staff_can_update_shop(self, client, shop_user, shop2):
        """店舗スタッフは所属店舗を変更できる"""
        client.force_login(shop_user)
        url = reverse('user_update', kwargs={'pk': shop_user.pk})
        response = client.post(url, {
            'username': shop_user.username,
            'user_gender': shop_user.user_gender,
            'authority': shop_user.authority_id,
            'shop': shop2.pk,
            'new_password1': '',
            'new_password2': '',
        })
        assert response.status_code == 302
        shop_user.refresh_from_db()
        assert shop_user.shop_id == shop2.pk

    def test_shop_staff_cannot_change_restricted_fields(self, client, shop_user, authority_admin):
        """店舗スタッフは権限・ユーザー名など制限フィールドを変更できない"""
        client.force_login(shop_user)
        url = reverse('user_update', kwargs={'pk': shop_user.pk})
        original_username = shop_user.username
        response = client.post(url, {
            'username': 'hacked_name',
            'user_gender': 2,
            'authority': authority_admin.pk,  # 権限昇格を試みる
            'shop': shop_user.shop_id,
            'new_password1': '',
            'new_password2': '',
        })
        assert response.status_code == 302
        shop_user.refresh_from_db()
        assert shop_user.username == original_username
        assert shop_user.authority_id == 2  # 管理者に昇格していない

    # ---- 倉庫スタッフ ----

    def test_warehouse_staff_only_warehouse_field_editable(self, client, warehouse_user):
        """倉庫スタッフは所属倉庫のみ編集可能、他フィールドは disabled"""
        client.force_login(warehouse_user)
        response = client.get(reverse('user_update', kwargs={'pk': warehouse_user.pk}))
        form = response.context['form']
        assert form.fields['username'].disabled
        assert form.fields['user_gender'].disabled
        assert form.fields['authority'].disabled
        assert 'shop' not in form.fields

    def test_warehouse_staff_no_delete_button(self, client, warehouse_user):
        """倉庫スタッフは削除ボタンが非表示"""
        client.force_login(warehouse_user)
        response = client.get(reverse('user_update', kwargs={'pk': warehouse_user.pk}))
        # 削除モーダルを開くトリガーボタンが存在しない
        assert 'data-bs-target="#deleteModal"' not in response.content.decode()

    def test_warehouse_staff_can_update_warehouse(self, client, warehouse_user, warehouse2):
        """倉庫スタッフは所属倉庫を変更できる"""
        client.force_login(warehouse_user)
        url = reverse('user_update', kwargs={'pk': warehouse_user.pk})
        response = client.post(url, {
            'username': warehouse_user.username,
            'user_gender': warehouse_user.user_gender,
            'authority': warehouse_user.authority_id,
            'warehouse': warehouse2.pk,
            'new_password1': '',
            'new_password2': '',
        })
        assert response.status_code == 302
        warehouse_user.refresh_from_db()
        assert warehouse_user.warehouse_id == warehouse2.pk

    def test_warehouse_staff_cannot_change_restricted_fields(self, client, warehouse_user, authority_admin):
        """倉庫スタッフは権限・ユーザー名など制限フィールドを変更できない"""
        client.force_login(warehouse_user)
        url = reverse('user_update', kwargs={'pk': warehouse_user.pk})
        original_username = warehouse_user.username
        response = client.post(url, {
            'username': 'hacked_name',
            'user_gender': 2,
            'authority': authority_admin.pk,
            'warehouse': warehouse_user.warehouse_id,
            'new_password1': '',
            'new_password2': '',
        })
        assert response.status_code == 302
        warehouse_user.refresh_from_db()
        assert warehouse_user.username == original_username
        assert warehouse_user.authority_id == 3  # 管理者に昇格していない


# ---------------------------------------------------------------------------
# 論理削除
# ---------------------------------------------------------------------------

class TestUserDelete:
    def test_delete_sets_delete_flg(self, client, admin_user, shop_user):
        """削除ボタン押下で delete_flg が True になる"""
        client.force_login(admin_user)
        url = reverse('user_delete', kwargs={'pk': shop_user.pk})
        response = client.post(url)
        assert response.status_code == 302
        shop_user.refresh_from_db()
        assert shop_user.delete_flg is True

    def test_deleted_user_not_in_active_objects(self, client, admin_user, shop_user):
        """論理削除後は active_objects に含まれない"""
        client.force_login(admin_user)
        client.post(reverse('user_delete', kwargs={'pk': shop_user.pk}))
        assert not User.active_objects.filter(pk=shop_user.pk).exists()


# ---------------------------------------------------------------------------
# 論理削除済みユーザーのログイン制限
# ---------------------------------------------------------------------------

class TestLoginWithDeletedUser:
    def test_deleted_user_cannot_login(self, client, deleted_user):
        """論理削除済みユーザーはログインが拒否される"""
        response = client.post(reverse('login'), {
            'username': 'deleted_user',
            'password': 'testpass123',
        })
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_active_user_can_login(self, client, admin_user):
        """論理削除されていない正常ユーザーは引き続きログインできる"""
        response = client.post(reverse('login'), {
            'username': 'admin_user',
            'password': 'testpass123',
        })
        assert response.status_code == 302
        assert response.url == '/'


# ---------------------------------------------------------------------------
# seed_master マネジメントコマンド
# ---------------------------------------------------------------------------

class TestSeedMasterCommand:

    def test_creates_all_authorities(self, db):
        """コマンド実行後に Authority が3件（id=1,2,3）作成される"""
        call_command('seed_master')
        assert Authority.objects.filter(id=1, authority_name='管理者').exists()
        assert Authority.objects.filter(id=2, authority_name='店舗スタッフ').exists()
        assert Authority.objects.filter(id=3, authority_name='倉庫スタッフ').exists()
        assert Authority.objects.count() == 3

    def test_creates_superuser(self, db):
        """コマンド実行後にスーパーユーザー admin が作成される"""
        call_command('seed_master')
        user = User.objects.get(username='admin')
        assert user.is_superuser is True
        assert user.authority_id == 1

    def test_superuser_can_login(self, db, client):
        """作成されたスーパーユーザー（admin/password）でログインできる"""
        call_command('seed_master')
        response = client.post(reverse('login'), {
            'username': 'admin',
            'password': 'password',
        })
        assert response.status_code == 302
        assert response.url == '/'

    def test_idempotent_authorities(self, db):
        """2回実行しても Authority は重複作成されない"""
        call_command('seed_master')
        call_command('seed_master')
        assert Authority.objects.count() == 3

    def test_idempotent_superuser(self, db):
        """2回実行しても superuser は重複作成されない"""
        call_command('seed_master')
        call_command('seed_master')
        assert User.objects.filter(username='admin').count() == 1

    def test_existing_authority_not_overwritten(self, db):
        """既存の Authority レコードがあっても上書きされない（get_or_create のスキップ動作）"""
        Authority.objects.create(id=1, authority_name='既存データ')
        call_command('seed_master')
        assert Authority.objects.get(id=1).authority_name == '既存データ'

    def test_existing_superuser_not_overwritten(self, db):
        """同名ユーザーが既に存在する場合は作成をスキップする"""
        # 事前に Authority を作成してからユーザーを作成
        authority = Authority.objects.create(id=1, authority_name='管理者')
        Authority.objects.create(id=2, authority_name='店舗スタッフ')
        Authority.objects.create(id=3, authority_name='倉庫スタッフ')
        User.objects.create_superuser(
            username='admin',
            password='differentpassword',
            user_gender=1,
            authority=authority,
        )
        call_command('seed_master')
        # ユーザーは1件のまま、パスワードも変わっていない
        assert User.objects.filter(username='admin').count() == 1
        user = User.objects.get(username='admin')
        assert user.check_password('differentpassword')
