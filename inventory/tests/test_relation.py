import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from inventory.models import Order, OrderGoods, Relation, Shop, Warehouse

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# 連携情報削除
# ---------------------------------------------------------------------------

class TestRelationDelete:

    def test_unauthenticated_redirect(self, client, relation):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, relation):
        """店舗スタッフは連携情報削除にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, relation):
        """倉庫スタッフは連携情報削除にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        assert response.status_code == 403

    def test_admin_can_delete_relation(self, client, admin_user, relation):
        """管理者は発注・問い合わせが存在しない連携情報を削除できる"""
        client.force_login(admin_user)
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        assert response.status_code == 302
        relation.refresh_from_db()
        assert relation.delete_flg is True

    def test_delete_success_message(self, client, admin_user, relation):
        """削除成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除しました' in str(m) for m in msgs)

    def test_delete_redirects_to_relation_list(self, client, admin_user, relation):
        """削除後は連携情報一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        assert response.url == reverse('relation_list')

    def test_cannot_delete_relation_with_active_order(self, client, admin_user, relation, goods):
        """発注が紐づく連携情報は削除できない"""
        order = Order.objects.create(relation=relation)
        OrderGoods.objects.create(order=order, goods=goods, quantity=1)
        client.force_login(admin_user)
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        relation.refresh_from_db()
        assert relation.delete_flg is False
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除できません' in str(m) for m in msgs)

    def test_cannot_delete_relation_with_active_inquiry(self, client, admin_user, relation, inquiry_to_warehouse):
        """問い合わせが紐づく連携情報は削除できない"""
        client.force_login(admin_user)
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        relation.refresh_from_db()
        assert relation.delete_flg is False
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除できません' in str(m) for m in msgs)

    def test_delete_with_next_param_redirects(self, client, admin_user, relation):
        """next パラメータがある場合そちらにリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(
            reverse('relation_delete', kwargs={'pk': relation.pk}),
            {'next': reverse('relation_list')},
        )
        assert response.url == reverse('relation_list')

    def test_get_not_found_for_deleted_relation(self, client, admin_user, relation):
        """論理削除済みの連携情報に対する削除リクエストは 404 になる"""
        relation.soft_delete()
        client.force_login(admin_user)
        response = client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        assert response.status_code == 404

    def test_deleted_relation_excluded_from_active_objects(self, client, admin_user, relation):
        """削除後は active_objects に含まれない"""
        client.force_login(admin_user)
        client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        assert not Relation.active_objects.filter(pk=relation.pk).exists()

    def test_can_recreate_relation_after_delete(self, client, admin_user, shop, warehouse, relation):
        """削除後に同じ店舗・倉庫の組み合わせで再連携できる"""
        # 削除
        client.force_login(admin_user)
        client.post(reverse('relation_delete', kwargs={'pk': relation.pk}))
        # 再連携
        response = client.post(
            reverse('relation_create'),
            {'shop': shop.pk, 'warehouse': warehouse.pk},
        )
        assert response.status_code == 302
        assert Relation.active_objects.filter(shop=shop, warehouse=warehouse).exists()


# ---------------------------------------------------------------------------
# 連携情報一覧
# ---------------------------------------------------------------------------

class TestRelationList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('relation_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは連携情報一覧にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('relation_list'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは連携情報一覧にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('relation_list'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user, relation):
        """管理者は連携情報一覧を表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('relation_list'))
        assert response.status_code == 200

    def test_shop_list_in_context(self, client, admin_user, shop, relation):
        """shop_list がコンテキストに含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('relation_list'))
        shop_ids = [s.pk for s in response.context['shop_list']]
        assert shop.pk in shop_ids

    def test_shop_name_filter(self, client, admin_user, shop, shop2, relation):
        """店舗名キーワードで絞り込むと一致する店舗のみ表示される"""
        client.force_login(admin_user)
        # '店舗2' は shop2.shop_name='テスト店舗2' にのみマッチし
        # shop.shop_name='テスト店舗' にはマッチしない
        response = client.get(reverse('relation_list') + '?shop_name=店舗2')
        shop_ids = [s.pk for s in response.context['shop_list']]
        assert shop2.pk in shop_ids
        assert shop.pk not in shop_ids


# ---------------------------------------------------------------------------
# 連携情報作成
# ---------------------------------------------------------------------------

class TestRelationCreate:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('relation_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは連携情報作成にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('relation_create'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは連携情報作成にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('relation_create'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user):
        """管理者は連携情報作成フォームを表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('relation_create'))
        assert response.status_code == 200

    def test_valid_post_creates_relation(self, client, admin_user, shop, warehouse):
        """有効なデータを POST すると連携情報が作成される"""
        client.force_login(admin_user)
        client.post(reverse('relation_create'), {'shop': shop.pk, 'warehouse': warehouse.pk})
        assert Relation.active_objects.filter(shop=shop, warehouse=warehouse).exists()

    def test_valid_post_redirects_to_list(self, client, admin_user, shop, warehouse):
        """POST 成功後は連携情報一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('relation_create'), {
            'shop': shop.pk,
            'warehouse': warehouse.pk,
        })
        assert response.status_code == 302
        assert response.url == reverse('relation_list')

    def test_valid_post_shows_success_message(self, client, admin_user, shop, warehouse):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('relation_create'), {
            'shop': shop.pk,
            'warehouse': warehouse.pk,
        })
        msgs = list(get_messages(response.wsgi_request))
        assert any('登録しました' in str(m) for m in msgs)

    def test_duplicate_relation_shows_form_error(self, client, admin_user, relation, shop, warehouse):
        """同一店舗・倉庫の組み合わせは重複エラーになる"""
        # relation fixture で shop↔warehouse はすでに連携済み
        client.force_login(admin_user)
        response = client.post(reverse('relation_create'), {
            'shop': shop.pk,
            'warehouse': warehouse.pk,
        })
        assert response.status_code == 200
        assert response.context['form'].non_field_errors()


# ---------------------------------------------------------------------------
# 店舗連携倉庫一覧（店舗スタッフ向け）
# ---------------------------------------------------------------------------

class TestShopConnectedWarehouseList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('shop_connected_warehouse_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は店舗連携倉庫一覧にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_connected_warehouse_list'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは店舗連携倉庫一覧にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('shop_connected_warehouse_list'))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user):
        """店舗スタッフは店舗連携倉庫一覧を表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_connected_warehouse_list'))
        assert response.status_code == 200

    def test_connected_warehouse_in_relations(self, client, shop_user, relation):
        """連携している倉庫が relations コンテキストに含まれる"""
        # relation: shop_user.shop ↔ warehouse
        client.force_login(shop_user)
        response = client.get(reverse('shop_connected_warehouse_list'))
        relation_ids = [r.pk for r in response.context['relations']]
        assert relation.pk in relation_ids

    def test_unconnected_warehouse_not_in_relations(self, client, shop_user, warehouse2):
        """連携していない倉庫は relations に含まれない"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_connected_warehouse_list'))
        warehouse_ids = [r.warehouse.pk for r in response.context['relations']]
        assert warehouse2.pk not in warehouse_ids
