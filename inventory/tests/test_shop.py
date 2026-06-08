import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from inventory.models import Shop, ShopStock

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# テスト用ヘルパー fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def shop_stock(db, goods, shop_user):
    """shop_user の店舗に紐づく ShopStock（stock=50）"""
    return ShopStock.objects.create(shop=shop_user.shop, goods=goods, stock=50)


# ---------------------------------------------------------------------------
# 店舗在庫一覧
# ---------------------------------------------------------------------------

class TestShopStockList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('shop_stock_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は店舗在庫一覧にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_stock_list'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは店舗在庫一覧にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('shop_stock_list'))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user, goods):
        """店舗スタッフは店舗在庫一覧を表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_list'))
        assert response.status_code == 200
        assert 'shop_stock_list' in response.context

    def test_stock_annotated_zero_without_record(self, client, shop_user, goods):
        """ShopStock レコードがない商品は在庫数が 0 でアノテートされる"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_list'))
        item = next(g for g in response.context['shop_stock_list'] if g.pk == goods.pk)
        assert item.stock == 0

    def test_stock_annotated_correctly_with_record(self, client, shop_user, goods, shop_stock):
        """ShopStock レコードがある商品は正しい在庫数がアノテートされる"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_list'))
        item = next(g for g in response.context['shop_stock_list'] if g.pk == goods.pk)
        assert item.stock == shop_stock.stock  # 50

    def test_category_filter_includes_matching(self, client, shop_user, goods, goods_category):
        """カテゴリ絞り込みで一致する商品が表示される"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_list') + f'?category={goods_category.id}')
        assert response.status_code == 200
        pks = [g.pk for g in response.context['shop_stock_list']]
        assert goods.pk in pks

    def test_category_filter_excludes_non_matching(self, client, shop_user, goods):
        """存在しないカテゴリ ID で絞り込むと商品が表示されない"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_list') + '?category=99999')
        assert response.status_code == 200
        assert len(response.context['shop_stock_list']) == 0


# ---------------------------------------------------------------------------
# 店舗在庫編集
# ---------------------------------------------------------------------------

class TestShopStockEdit:

    def test_unauthenticated_redirect(self, client, goods):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user, goods):
        """管理者は店舗在庫編集にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, goods):
        """倉庫スタッフは店舗在庫編集にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user, goods):
        """店舗スタッフは店舗在庫編集フォームを表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'goods' in response.context

    def test_get_shows_goods_name(self, client, shop_user, goods):
        """編集画面に商品名が表示される"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert goods.goods_name in response.content.decode()

    def test_get_form_has_instance_when_record_exists(self, client, shop_user, goods, shop_stock):
        """ShopStock レコードがある場合、フォームのインスタンスに既存レコードがセットされる"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}))
        form = response.context['form']
        assert form.instance.pk == shop_stock.pk
        assert form.instance.stock == shop_stock.stock

    def test_get_form_has_no_instance_without_record(self, client, shop_user, goods):
        """ShopStock レコードがない場合、フォームのインスタンスは未保存状態になる"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}))
        form = response.context['form']
        assert form.instance.pk is None

    def test_nonexistent_goods_returns_404(self, client, shop_user):
        """存在しない goods_pk を指定すると 404 になる"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_stock_edit', kwargs={'goods_pk': 99999}))
        assert response.status_code == 404

    def test_post_creates_shop_stock_when_no_record(self, client, shop_user, goods):
        """ShopStock レコードがない状態で POST すると新規作成される"""
        client.force_login(shop_user)
        client.post(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}), {'stock': 30})
        assert ShopStock.objects.filter(goods=goods, shop=shop_user.shop, stock=30).exists()

    def test_post_updates_shop_stock_when_record_exists(self, client, shop_user, goods, shop_stock):
        """既存の ShopStock レコードがある状態で POST すると在庫数が更新される"""
        client.force_login(shop_user)
        client.post(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}), {'stock': 99})
        shop_stock.refresh_from_db()
        assert shop_stock.stock == 99

    def test_post_does_not_duplicate_record(self, client, shop_user, goods, shop_stock):
        """POST を複数回行っても ShopStock レコードが重複して作成されない"""
        client.force_login(shop_user)
        client.post(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}), {'stock': 10})
        client.post(reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}), {'stock': 20})
        assert ShopStock.objects.filter(goods=goods, shop=shop_user.shop).count() == 1

    def test_post_valid_redirects_to_list(self, client, shop_user, goods):
        """有効なデータを POST すると店舗在庫一覧にリダイレクトされる"""
        client.force_login(shop_user)
        response = client.post(
            reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}), {'stock': 10}
        )
        assert response.status_code == 302
        assert response.url == reverse('shop_stock_list')

    def test_post_negative_stock_shows_error(self, client, shop_user, goods):
        """マイナスの在庫数を POST するとバリデーションエラーになる"""
        client.force_login(shop_user)
        response = client.post(
            reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}), {'stock': -1}
        )
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_post_empty_stock_shows_error(self, client, shop_user, goods):
        """在庫数を空で POST するとバリデーションエラーになる"""
        client.force_login(shop_user)
        response = client.post(
            reverse('shop_stock_edit', kwargs={'goods_pk': goods.pk}), {'stock': ''}
        )
        assert response.status_code == 200
        assert response.context['form'].errors


# ---------------------------------------------------------------------------
# 店舗削除
# ---------------------------------------------------------------------------

class TestShopDelete:

    def test_unauthenticated_redirect(self, client, shop):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, shop):
        """店舗スタッフは店舗削除にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, shop):
        """倉庫スタッフは店舗削除にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        assert response.status_code == 403

    def test_admin_can_delete_shop(self, client, admin_user, shop):
        """管理者は連携情報・所属ユーザー等が存在しない店舗を削除できる"""
        client.force_login(admin_user)
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        assert response.status_code == 302
        shop.refresh_from_db()
        assert shop.delete_flg is True

    def test_delete_success_message(self, client, admin_user, shop):
        """削除成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除しました' in str(m) for m in msgs)

    def test_delete_redirects_to_shop_list(self, client, admin_user, shop):
        """削除後は店舗一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        assert response.url == reverse('shop_list')

    def test_cannot_delete_shop_with_relation(self, client, admin_user, shop, relation):
        """連携情報に紐づく店舗は削除できない"""
        client.force_login(admin_user)
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        shop.refresh_from_db()
        assert shop.delete_flg is False
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除できません' in str(m) for m in msgs)

    def test_cannot_delete_shop_with_user(self, client, admin_user, shop, shop_user):
        """所属ユーザーに紐づく店舗は削除できない"""
        client.force_login(admin_user)
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        shop.refresh_from_db()
        assert shop.delete_flg is False

    def test_delete_with_next_param_redirects(self, client, admin_user, shop):
        """next パラメータがある場合そちらにリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(
            reverse('shop_delete', kwargs={'pk': shop.pk}),
            {'next': reverse('shop_list')},
        )
        assert response.url == reverse('shop_list')

    def test_get_not_found_for_deleted_shop(self, client, admin_user, shop):
        """論理削除済みの店舗に対する削除リクエストは 404 になる"""
        shop.delete_flg = True
        shop.save()
        client.force_login(admin_user)
        response = client.post(reverse('shop_delete', kwargs={'pk': shop.pk}))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 店舗一覧
# ---------------------------------------------------------------------------

class TestShopList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('shop_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは店舗一覧にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_list'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは店舗一覧にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('shop_list'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user, shop):
        """管理者は店舗一覧を表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_list'))
        assert response.status_code == 200

    def test_shop_in_context(self, client, admin_user, shop):
        """店舗が shops コンテキストに含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_list'))
        ids = [s.pk for s in response.context['shops']]
        assert shop.pk in ids

    def test_deleted_shop_excluded(self, client, admin_user, shop):
        """論理削除済みの店舗は一覧に表示されない"""
        shop.soft_delete()
        client.force_login(admin_user)
        response = client.get(reverse('shop_list'))
        ids = [s.pk for s in response.context['shops']]
        assert shop.pk not in ids

    def test_address_filter(self, client, admin_user, shop, shop2):
        """都道府県で絞り込むと一致する店舗のみ表示される"""
        # shop は '東京都', shop2 は '大阪府'
        client.force_login(admin_user)
        response = client.get(reverse('shop_list') + '?prefecture=東京都')
        ids = [s.pk for s in response.context['shops']]
        assert shop.pk in ids
        assert shop2.pk not in ids


# ---------------------------------------------------------------------------
# 店舗追加
# ---------------------------------------------------------------------------

class TestShopCreate:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('shop_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは店舗追加にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_create'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは店舗追加にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('shop_create'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user):
        """管理者は店舗追加フォームを表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_create'))
        assert response.status_code == 200

    def test_valid_post_creates_shop(self, client, admin_user):
        """有効なデータを POST すると店舗が作成される"""
        client.force_login(admin_user)
        client.post(reverse('shop_create'), {
            'shop_name': '新店舗',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        assert Shop.objects.filter(shop_name='新店舗').exists()

    def test_valid_post_redirects_to_list(self, client, admin_user):
        """POST 成功後は店舗一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('shop_create'), {
            'shop_name': '新店舗',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        assert response.status_code == 302
        assert response.url == reverse('shop_list')

    def test_valid_post_shows_success_message(self, client, admin_user):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('shop_create'), {
            'shop_name': '新店舗',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        msgs = list(get_messages(response.wsgi_request))
        assert any('登録しました' in str(m) for m in msgs)


# ---------------------------------------------------------------------------
# 店舗編集
# ---------------------------------------------------------------------------

class TestShopUpdate:

    def test_unauthenticated_redirect(self, client, shop):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('shop_edit', kwargs={'pk': shop.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは店舗編集にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('shop_edit', kwargs={'pk': shop_user.shop.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, shop):
        """倉庫スタッフは店舗編集にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('shop_edit', kwargs={'pk': shop.pk}))
        assert response.status_code == 403

    def test_admin_get_200_with_form(self, client, admin_user, shop):
        """管理者は店舗編集フォームを表示でき、既存データがセットされる"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_edit', kwargs={'pk': shop.pk}))
        assert response.status_code == 200
        assert response.context['form'].instance == shop

    def test_valid_post_updates_shop(self, client, admin_user, shop):
        """有効なデータを POST すると店舗名が更新される"""
        client.force_login(admin_user)
        client.post(reverse('shop_edit', kwargs={'pk': shop.pk}), {
            'shop_name': '更新店舗',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        shop.refresh_from_db()
        assert shop.shop_name == '更新店舗'

    def test_valid_post_shows_success_message(self, client, admin_user, shop):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('shop_edit', kwargs={'pk': shop.pk}), {
            'shop_name': '更新店舗',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        msgs = list(get_messages(response.wsgi_request))
        assert any('更新しました' in str(m) for m in msgs)

    def test_can_delete_true_without_related(self, client, admin_user, shop):
        """ユーザー・在庫・連携が紐づかない場合 can_delete=True"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_edit', kwargs={'pk': shop.pk}))
        assert response.context['can_delete'] is True

    def test_can_delete_false_with_relation(self, client, admin_user, shop, relation):
        """連携情報が紐づく場合 can_delete=False"""
        client.force_login(admin_user)
        response = client.get(reverse('shop_edit', kwargs={'pk': shop.pk}))
        assert response.context['can_delete'] is False
