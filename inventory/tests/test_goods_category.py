import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from inventory.models import GoodsCategory

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# 商品カテゴリ一覧
# ---------------------------------------------------------------------------

class TestGoodsCategoryList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('goods_category_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは商品カテゴリ一覧にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('goods_category_list'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは商品カテゴリ一覧にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('goods_category_list'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user, goods_category):
        """管理者は商品カテゴリ一覧を表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_category_list'))
        assert response.status_code == 200

    def test_category_in_context(self, client, admin_user, goods_category):
        """商品カテゴリが category_list コンテキストに含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_category_list'))
        ids = [c.pk for c in response.context['category_list']]
        assert goods_category.pk in ids

    def test_deleted_category_excluded(self, client, admin_user, goods_category):
        """論理削除済みのカテゴリは一覧に表示されない"""
        goods_category.soft_delete()
        client.force_login(admin_user)
        response = client.get(reverse('goods_category_list'))
        ids = [c.pk for c in response.context['category_list']]
        assert goods_category.pk not in ids


# ---------------------------------------------------------------------------
# 商品カテゴリ作成
# ---------------------------------------------------------------------------

class TestGoodsCategoryCreate:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(reverse('goods_category_create'), {'category_name': 'テスト'})
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは商品カテゴリ作成にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.post(reverse('goods_category_create'), {'category_name': 'テスト'})
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは商品カテゴリ作成にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.post(reverse('goods_category_create'), {'category_name': 'テスト'})
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user):
        """管理者は商品カテゴリ作成フォームを表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_category_create'))
        assert response.status_code == 200

    def test_valid_post_creates_category(self, client, admin_user):
        """有効なデータを POST すると商品カテゴリが作成される"""
        client.force_login(admin_user)
        client.post(reverse('goods_category_create'), {'category_name': '新カテゴリ'})
        assert GoodsCategory.objects.filter(category_name='新カテゴリ').exists()

    def test_valid_post_redirects_to_list(self, client, admin_user):
        """POST 成功後は商品カテゴリ一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_category_create'), {'category_name': '新カテゴリ'})
        assert response.status_code == 302
        assert response.url == reverse('goods_category_list')

    def test_valid_post_shows_success_message(self, client, admin_user):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_category_create'), {'category_name': '新カテゴリ'})
        msgs = list(get_messages(response.wsgi_request))
        assert any('登録しました' in str(m) for m in msgs)

    def test_invalid_post_shows_form_errors(self, client, admin_user):
        """空のカテゴリ名を POST するとバリデーションエラーになる"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_category_create'), {'category_name': ''})
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_next_param_success_appends_category_created(self, client, admin_user):
        """next パラメータありで登録成功すると category_created が付いた URL にリダイレクト"""
        next_url = reverse('goods_create')
        client.force_login(admin_user)
        response = client.post(
            reverse('goods_category_create'),
            {'category_name': '新カテゴリ', 'next': next_url},
        )
        assert response.status_code == 302
        assert 'category_created' in response.url

    def test_next_param_error_redirects_to_next(self, client, admin_user, goods_category):
        """next パラメータありでバリデーションエラーの場合は next にリダイレクト"""
        next_url = reverse('goods_create')
        client.force_login(admin_user)
        # 既存のカテゴリ名で重複エラーを起こす
        response = client.post(
            reverse('goods_category_create'),
            {'category_name': goods_category.category_name, 'next': next_url},
        )
        assert response.status_code == 302
        assert response.url == next_url


# ---------------------------------------------------------------------------
# 商品カテゴリ編集
# ---------------------------------------------------------------------------

class TestGoodsCategoryUpdate:

    def test_unauthenticated_redirect(self, client, goods_category):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('goods_category_edit', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, goods_category):
        """店舗スタッフは商品カテゴリ編集にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('goods_category_edit', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, goods_category):
        """倉庫スタッフは商品カテゴリ編集にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('goods_category_edit', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 403

    def test_admin_get_200_with_form(self, client, admin_user, goods_category):
        """管理者は商品カテゴリ編集フォームを表示でき、既存データがセットされる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_category_edit', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 200
        assert response.context['form'].instance == goods_category

    def test_valid_post_updates_category(self, client, admin_user, goods_category):
        """有効なデータを POST するとカテゴリ名が更新される"""
        client.force_login(admin_user)
        client.post(
            reverse('goods_category_edit', kwargs={'pk': goods_category.pk}),
            {'category_name': '更新カテゴリ'},
        )
        goods_category.refresh_from_db()
        assert goods_category.category_name == '更新カテゴリ'

    def test_valid_post_shows_success_message(self, client, admin_user, goods_category):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(
            reverse('goods_category_edit', kwargs={'pk': goods_category.pk}),
            {'category_name': '更新カテゴリ'},
        )
        msgs = list(get_messages(response.wsgi_request))
        assert any('更新しました' in str(m) for m in msgs)

    def test_can_delete_true_without_goods(self, client, admin_user, goods_category):
        """商品が紐づいていない場合 can_delete=True がコンテキストにセットされる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_category_edit', kwargs={'pk': goods_category.pk}))
        assert response.context['can_delete'] is True

    def test_can_delete_false_with_goods(self, client, admin_user, goods_category, goods):
        """商品が紐づいている場合 can_delete=False がコンテキストにセットされる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_category_edit', kwargs={'pk': goods_category.pk}))
        assert response.context['can_delete'] is False


# ---------------------------------------------------------------------------
# 商品カテゴリ削除
# ---------------------------------------------------------------------------

class TestGoodsCategoryDelete:

    def test_unauthenticated_redirect(self, client, goods_category):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(reverse('goods_category_delete', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, goods_category):
        """店舗スタッフは商品カテゴリ削除にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.post(reverse('goods_category_delete', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, goods_category):
        """倉庫スタッフは商品カテゴリ削除にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.post(reverse('goods_category_delete', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 403

    def test_admin_can_delete_category(self, client, admin_user, goods_category):
        """管理者は商品が紐づかないカテゴリを削除できる"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_category_delete', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 302
        goods_category.refresh_from_db()
        assert goods_category.delete_flg is True

    def test_delete_success_message(self, client, admin_user, goods_category):
        """削除成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_category_delete', kwargs={'pk': goods_category.pk}))
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除しました' in str(m) for m in msgs)

    def test_delete_redirects_to_list(self, client, admin_user, goods_category):
        """削除後は商品カテゴリ一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_category_delete', kwargs={'pk': goods_category.pk}))
        assert response.url == reverse('goods_category_list')

    def test_cannot_delete_category_with_goods(self, client, admin_user, goods_category, goods):
        """商品が紐づくカテゴリは削除できない"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_category_delete', kwargs={'pk': goods_category.pk}))
        goods_category.refresh_from_db()
        assert goods_category.delete_flg is False
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除できません' in str(m) for m in msgs)

    def test_not_found_for_deleted_category(self, client, admin_user, goods_category):
        """論理削除済みのカテゴリに対する削除リクエストは 404 になる"""
        goods_category.soft_delete()
        client.force_login(admin_user)
        response = client.post(reverse('goods_category_delete', kwargs={'pk': goods_category.pk}))
        assert response.status_code == 404
