"""
ShopDetailView と RelationConnectView のテスト

【テストファイルの構成について】
- クラスで機能ごとにテストをグループ化する
- 各メソッドに docstring でテストの意図を書く
- 1つのテストメソッドで1つのことだけを確認する（単一責任）

【pytestmark について】
- ファイル内の全テストに `pytest.mark.django_db` を付与する設定
- これがないとDBアクセスが許可されずエラーになる
"""
import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from inventory.models import Relation, Warehouse

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# テスト用フィクスチャ
#
# 【フィクスチャとは】
# テストで繰り返し使うデータをあらかじめ用意しておく仕組み。
# conftest.py に共通フィクスチャ（shop, warehouse, admin_user など）が定義されている。
# ここではこのテストファイル専用のフィクスチャを追加で定義する。
# ---------------------------------------------------------------------------

@pytest.fixture
def warehouse2(db):
    """都道府県が異なる2つ目の倉庫（大阪府）"""
    return Warehouse.objects.create(
        warehouse_name='大阪倉庫',
        prefecture='大阪府',
        city='大阪市',
        address1='1-1-1',
    )


@pytest.fixture
def relation(db, shop, warehouse):
    """shop と warehouse を連携済みにする"""
    return Relation.objects.create(shop=shop, warehouse=warehouse)


# ---------------------------------------------------------------------------
# ShopDetailView のテスト
#
# 【テストする観点】
# 1. アクセス制御（誰がアクセスできるか）
# 2. 正常系（正しくデータが表示されるか）
# 3. 検索・絞り込み機能（フィルターが正しく動くか）
# ---------------------------------------------------------------------------

class TestShopDetailView:

    # --- アクセス制御 ---

    def test_unauthenticated_redirect(self, client, shop):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        # 【ポイント】
        # force_login を使わずにアクセスすると未ログイン扱いになる
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, shop):
        """店舗スタッフは店舗詳細にアクセスできない（403）"""
        # 【ポイント】
        # AdminRequiredMixin が付いているビューは管理者以外 403 を返す
        client.force_login(shop_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, shop):
        """倉庫スタッフは店舗詳細にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user, shop):
        """管理者は店舗詳細を表示できる（200）"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        assert response.status_code == 200

    def test_nonexistent_shop_returns_404(self, client, admin_user):
        """存在しない pk を指定すると 404 になる"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': 99999}))
        assert response.status_code == 404

    # --- コンテキストの確認 ---

    def test_context_contains_shop(self, client, admin_user, shop):
        """context に shop オブジェクトが含まれる"""
        # 【ポイント】
        # response.context でテンプレートに渡された変数を確認できる
        client.force_login(admin_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        assert response.context['shop'] == shop

    def test_connected_relations_in_context(self, client, admin_user, shop, relation):
        """連携済み倉庫が connected_relations に含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        relation_ids = [r.pk for r in response.context['connected_relations']]
        assert relation.pk in relation_ids

    def test_not_connected_warehouses_in_context(self, client, admin_user, shop, warehouse2):
        """未連携倉庫が not_connected_warehouses に含まれる"""
        # warehouse2 は shop と連携していないので未連携として表示される
        client.force_login(admin_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        warehouse_ids = [w.pk for w in response.context['not_connected_warehouses']]
        assert warehouse2.pk in warehouse_ids

    def test_connected_warehouse_not_in_not_connected(self, client, admin_user, shop, warehouse, relation):
        """連携済み倉庫は未連携倉庫一覧に含まれない"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        warehouse_ids = [w.pk for w in response.context['not_connected_warehouses']]
        assert warehouse.pk not in warehouse_ids

    # --- 検索・絞り込み機能 ---

    def test_filter_by_status_connected(self, client, admin_user, shop, warehouse, warehouse2, relation):
        """status=connected で連携済みのみ表示され、未連携が空になる"""
        # 【ポイント】
        # GETパラメータは URL に ?key=value の形で渡す
        client.force_login(admin_user)
        url = reverse('shop_detail', kwargs={'pk': shop.pk}) + '?status=connected'
        response = client.get(url)
        assert list(response.context['not_connected_warehouses']) == []

    def test_filter_by_status_not_connected(self, client, admin_user, shop, warehouse, relation):
        """status=not_connected で未連携のみ表示され、連携済みが空になる"""
        client.force_login(admin_user)
        url = reverse('shop_detail', kwargs={'pk': shop.pk}) + '?status=not_connected'
        response = client.get(url)
        assert list(response.context['connected_relations']) == []

    def test_filter_by_prefecture(self, client, admin_user, shop, warehouse, warehouse2, relation):
        """都道府県で絞り込むと一致する倉庫のみ表示される"""
        # warehouse は東京都、warehouse2 は大阪府
        client.force_login(admin_user)
        url = reverse('shop_detail', kwargs={'pk': shop.pk}) + '?prefecture=大阪府'
        response = client.get(url)
        warehouse_ids = [w.pk for w in response.context['not_connected_warehouses']]
        assert warehouse2.pk in warehouse_ids
        assert warehouse.pk not in warehouse_ids

    def test_filter_by_name(self, client, admin_user, shop, warehouse2):
        """倉庫名で絞り込むと一致する倉庫のみ表示される"""
        client.force_login(admin_user)
        url = reverse('shop_detail', kwargs={'pk': shop.pk}) + '?q=大阪'
        response = client.get(url)
        warehouse_ids = [w.pk for w in response.context['not_connected_warehouses']]
        assert warehouse2.pk in warehouse_ids

    def test_filter_by_name_no_match(self, client, admin_user, shop):
        """一致しない倉庫名で検索すると結果が空になる"""
        client.force_login(admin_user)
        url = reverse('shop_detail', kwargs={'pk': shop.pk}) + '?q=存在しない倉庫名'
        response = client.get(url)
        assert list(response.context['not_connected_warehouses']) == []
        assert list(response.context['connected_relations']) == []

    def test_prefecture_choices_in_context(self, client, admin_user, shop):
        """都道府県の選択肢が context に含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_detail', kwargs={'pk': shop.pk}))
        assert 'prefecture_choices' in response.context

    def test_selected_filters_preserved_in_context(self, client, admin_user, shop):
        """絞り込み条件が context に保持される（フォームの値を維持するため）"""
        client.force_login(admin_user)
        url = reverse('shop_detail', kwargs={'pk': shop.pk}) + '?q=テスト&prefecture=東京都&status=connected'
        response = client.get(url)
        assert response.context['selected_q'] == 'テスト'
        assert response.context['selected_prefecture'] == '東京都'
        assert response.context['selected_status'] == 'connected'


# ---------------------------------------------------------------------------
# RelationConnectView のテスト
#
# 【テストする観点】
# 1. アクセス制御
# 2. 正常系（連携が作成されるか）
# 3. 異常系（既に連携済みの場合、存在しないIDの場合）
# ---------------------------------------------------------------------------

class TestRelationConnectView:

    def _post(self, client, shop, warehouse, next_url=None):
        """
        POST リクエストを送るヘルパーメソッド。
        【ポイント】
        テストコードの重複を減らすために共通処理をメソッドにまとめる。
        """
        data = {
            'shop_id': shop.pk,
            'warehouse_id': warehouse.pk,
        }
        if next_url:
            data['next'] = next_url
        return client.post(reverse('relation_connect'), data)

    # --- アクセス制御 ---

    def test_unauthenticated_redirect(self, client, shop, warehouse):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = self._post(client, shop, warehouse)
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, shop, warehouse):
        """店舗スタッフは連携作成にアクセスできない（403）"""
        client.force_login(shop_user)
        response = self._post(client, shop, warehouse)
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, shop, warehouse):
        """倉庫スタッフは連携作成にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = self._post(client, shop, warehouse)
        assert response.status_code == 403

    # --- 正常系 ---

    def test_creates_relation(self, client, admin_user, shop, warehouse):
        """管理者が POST すると連携レコードが作成される"""
        client.force_login(admin_user)
        self._post(client, shop, warehouse)
        assert Relation.active_objects.filter(shop=shop, warehouse=warehouse).exists()

    def test_success_message(self, client, admin_user, shop, warehouse):
        """連携成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = self._post(client, shop, warehouse)
        msgs = list(get_messages(response.wsgi_request))
        assert any('連携しました' in str(m) for m in msgs)

    def test_redirects_to_next(self, client, admin_user, shop, warehouse):
        """next パラメータがある場合そちらにリダイレクトされる"""
        client.force_login(admin_user)
        next_url = reverse('shop_detail', kwargs={'pk': shop.pk})
        response = self._post(client, shop, warehouse, next_url=next_url)
        assert response.status_code == 302
        assert response.url == next_url

    def test_redirects_to_relation_list_without_next(self, client, admin_user, shop, warehouse):
        """next パラメータがない場合は relation_list にリダイレクトされる"""
        client.force_login(admin_user)
        response = self._post(client, shop, warehouse)
        assert response.status_code == 302
        assert response.url == reverse('relation_list')

    # --- 異常系 ---

    def test_already_connected_shows_error(self, client, admin_user, shop, warehouse, relation):
        """既に連携済みの場合はエラーメッセージが表示される"""
        # 【ポイント】
        # relation フィクスチャで既に shop と warehouse は連携済み
        client.force_login(admin_user)
        response = self._post(client, shop, warehouse)
        msgs = list(get_messages(response.wsgi_request))
        assert any('既に連携済み' in str(m) for m in msgs)

    def test_already_connected_does_not_duplicate(self, client, admin_user, shop, warehouse, relation):
        """既に連携済みの場合は連携レコードが重複して作成されない"""
        client.force_login(admin_user)
        self._post(client, shop, warehouse)
        count = Relation.active_objects.filter(shop=shop, warehouse=warehouse).count()
        assert count == 1

    def test_invalid_shop_id_returns_404(self, client, admin_user, warehouse):
        """存在しない shop_id を指定すると 404 になる"""
        client.force_login(admin_user)
        response = client.post(reverse('relation_connect'), {
            'shop_id': 99999,
            'warehouse_id': warehouse.pk,
        })
        assert response.status_code == 404

    def test_invalid_warehouse_id_returns_404(self, client, admin_user, shop):
        """存在しない warehouse_id を指定すると 404 になる"""
        client.force_login(admin_user)
        response = client.post(reverse('relation_connect'), {
            'shop_id': shop.pk,
            'warehouse_id': 99999,
        })
        assert response.status_code == 404
