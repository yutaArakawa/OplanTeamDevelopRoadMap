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
# ユーザー一覧
# ---------------------------------------------------------------------------

class TestUserList:
    def test_list_page_accessible(self, client, admin_user):
        """ユーザー一覧ページに正常アクセスできる"""
        client.force_login(admin_user)
        response = client.get(reverse('user_list'))
        assert response.status_code == 200

    def test_mypage_button_shown_for_own_account(self, client, admin_user):
        """自分のアカウント行にマイページボタンが表示される"""
        client.force_login(admin_user)
        response = client.get(reverse('user_list'))
        assert reverse('mypage') in response.content.decode()

    def test_mypage_button_not_shown_for_other_accounts(self, client, admin_user, shop_user):
        """他ユーザーの行にはマイページボタンが表示されない（テーブル内は1件のみ）"""
        client.force_login(admin_user)
        response = client.get(reverse('user_list'))
        content = response.content.decode()
        # テーブル内のマイページリンクは自分の行の1件のみ
        assert content.count('btn-outline-primary">マイページ') == 1


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
