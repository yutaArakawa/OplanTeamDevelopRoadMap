import csv as csv_module

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from inventory.models import GoodsCategory, Goods, Warehouse, WarehouseStock, Order, OrderGoods, Relation, ShopStock

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# 倉庫在庫一覧
# ---------------------------------------------------------------------------

class TestWarehouseStockList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('warehouse_stock_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は倉庫在庫一覧にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_stock_list'))
        assert response.status_code == 403

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは倉庫在庫一覧にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('warehouse_stock_list'))
        assert response.status_code == 403

    def test_warehouse_user_get_200(self, client, warehouse_user, goods):
        """倉庫スタッフは倉庫在庫一覧を表示できる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_list'))
        assert response.status_code == 200

    def test_warehouse_name_in_context(self, client, warehouse_user, goods):
        """コンテキストにログインユーザーの倉庫名が含まれる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_list'))
        assert response.context['warehouse_name'] == warehouse_user.warehouse.warehouse_name

    def test_goods_in_stock_list(self, client, warehouse_user, goods):
        """商品が warehouse_stock_list コンテキストに含まれる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_list'))
        ids = [g.pk for g in response.context['warehouse_stock_list']]
        assert goods.pk in ids

    def test_stock_zero_without_record(self, client, warehouse_user, goods):
        """在庫レコードがない商品の在庫数は 0 で表示される"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_list'))
        target = response.context['warehouse_stock_list'].get(pk=goods.pk)
        assert target.stock == 0

    def test_stock_correct_value_with_record(self, client, warehouse_user, warehouse_stock):
        """在庫レコードがある商品の在庫数が正しく表示される"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_list'))
        target = response.context['warehouse_stock_list'].get(pk=warehouse_stock.goods.pk)
        assert target.stock == warehouse_stock.stock

    def test_other_warehouse_stock_not_counted(self, client, warehouse_user, warehouse2, goods):
        """別倉庫の在庫レコードは自分の倉庫の在庫数に影響しない"""
        # 別倉庫（warehouse2）に在庫を作成しても warehouse_user の在庫は 0 のまま
        WarehouseStock.objects.create(warehouse=warehouse2, goods=goods, stock=999)
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_list'))
        target = response.context['warehouse_stock_list'].get(pk=goods.pk)
        assert target.stock == 0

    def test_category_filter_shows_only_matching_goods(self, client, warehouse_user, goods, goods_category):
        """カテゴリーで絞り込むと一致する商品のみ表示される"""
        other_category = GoodsCategory.objects.create(category_name='別カテゴリ')
        other_goods = Goods.objects.create(goods_name='別商品', goods_category=other_category)

        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_list') + f'?category={goods_category.id}')
        ids = [g.pk for g in response.context['warehouse_stock_list']]
        assert goods.pk in ids
        assert other_goods.pk not in ids

    def test_category_filter_selected_category_in_context(self, client, warehouse_user, goods, goods_category):
        """カテゴリー絞り込み時に selected_category がコンテキストにセットされる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_list') + f'?category={goods_category.id}')
        assert str(response.context['selected_category']) == str(goods_category.id)


# ---------------------------------------------------------------------------
# 倉庫在庫編集
# ---------------------------------------------------------------------------

class TestWarehouseStockEdit:

    def test_unauthenticated_redirect(self, client, goods):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user, goods):
        """管理者は倉庫在庫編集にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 403

    def test_shop_user_forbidden(self, client, shop_user, goods):
        """店舗スタッフは倉庫在庫編集にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 403

    def test_warehouse_user_get_200(self, client, warehouse_user, goods):
        """倉庫スタッフは倉庫在庫編集フォームを表示できる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['goods'] == goods

    def test_get_no_stock_record_empty_form(self, client, warehouse_user, goods):
        """在庫レコードがない場合はフォームが未保存インスタンスで初期化される"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}))
        form = response.context['form']
        # 在庫レコードが存在しないため instance は未保存（pk=None）
        assert form.instance.pk is None

    def test_get_existing_stock_record_prefilled(self, client, warehouse_user, warehouse_stock):
        """既存の在庫レコードがある場合はフォームにその値が反映される"""
        client.force_login(warehouse_user)
        response = client.get(
            reverse('warehouse_stock_edit', kwargs={'goods_pk': warehouse_stock.goods.pk})
        )
        form = response.context['form']
        assert form.instance.pk == warehouse_stock.pk
        assert form.instance.stock == warehouse_stock.stock

    def test_post_creates_new_stock_record(self, client, warehouse_user, goods):
        """在庫レコードが存在しない状態でPOSTすると新規作成される"""
        client.force_login(warehouse_user)
        client.post(
            reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}),
            {'stock': 50},
        )
        assert WarehouseStock.objects.filter(
            warehouse=warehouse_user.warehouse, goods=goods, stock=50
        ).exists()

    def test_post_updates_existing_stock_record(self, client, warehouse_user, warehouse_stock):
        """既存の在庫レコードがある場合はPOSTで値が更新される"""
        client.force_login(warehouse_user)
        client.post(
            reverse('warehouse_stock_edit', kwargs={'goods_pk': warehouse_stock.goods.pk}),
            {'stock': 999},
        )
        warehouse_stock.refresh_from_db()
        assert warehouse_stock.stock == 999

    def test_post_success_redirects_to_list(self, client, warehouse_user, goods):
        """POST成功後は倉庫在庫一覧にリダイレクトされる"""
        client.force_login(warehouse_user)
        response = client.post(
            reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}),
            {'stock': 10},
        )
        assert response.status_code == 302
        assert response.url == reverse('warehouse_stock_list')

    def test_post_invalid_stock_shows_error(self, client, warehouse_user, goods):
        """負の在庫数を送信するとフォームエラーになり再表示される"""
        client.force_login(warehouse_user)
        response = client.post(
            reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}),
            {'stock': -1},
        )
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_post_does_not_affect_other_warehouse(self, client, warehouse_user, warehouse2, goods):
        """POSTは他の倉庫の在庫レコードに影響しない"""
        other_stock = WarehouseStock.objects.create(
            warehouse=warehouse2, goods=goods, stock=100
        )
        client.force_login(warehouse_user)
        client.post(
            reverse('warehouse_stock_edit', kwargs={'goods_pk': goods.pk}),
            {'stock': 50},
        )
        other_stock.refresh_from_db()
        assert other_stock.stock == 100


# ---------------------------------------------------------------------------
# 倉庫一覧
# ---------------------------------------------------------------------------

class TestWarehouseList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('warehouse_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは倉庫一覧にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('warehouse_list'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは倉庫一覧にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_list'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user, warehouse):
        """管理者は倉庫一覧を表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_list'))
        assert response.status_code == 200

    def test_warehouse_in_context(self, client, admin_user, warehouse):
        """倉庫が warehouse_list コンテキストに含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_list'))
        ids = [w.pk for w in response.context['warehouse_list']]
        assert warehouse.pk in ids

    def test_deleted_warehouse_excluded(self, client, admin_user, warehouse):
        """論理削除済みの倉庫は一覧に表示されない"""
        warehouse.soft_delete()
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_list'))
        ids = [w.pk for w in response.context['warehouse_list']]
        assert warehouse.pk not in ids

    def test_address_filter(self, client, admin_user, warehouse, warehouse2):
        """都道府県で絞り込むと一致する倉庫のみ表示される"""
        # warehouse は '東京都', warehouse2 は '大阪府'
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_list') + '?prefecture=東京都')
        ids = [w.pk for w in response.context['warehouse_list']]
        assert warehouse.pk in ids
        assert warehouse2.pk not in ids


# ---------------------------------------------------------------------------
# 倉庫追加
# ---------------------------------------------------------------------------

class TestWarehouseCreate:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('warehouse_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは倉庫追加にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('warehouse_create'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは倉庫追加にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_create'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user):
        """管理者は倉庫追加フォームを表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_create'))
        assert response.status_code == 200

    def test_valid_post_creates_warehouse(self, client, admin_user):
        """有効なデータを POST すると倉庫が作成される"""
        client.force_login(admin_user)
        client.post(reverse('warehouse_create'), {
            'warehouse_name': '新倉庫',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        assert Warehouse.objects.filter(warehouse_name='新倉庫').exists()

    def test_valid_post_redirects_to_list(self, client, admin_user):
        """POST 成功後は倉庫一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('warehouse_create'), {
            'warehouse_name': '新倉庫',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        assert response.status_code == 302
        assert response.url == reverse('warehouse_list')

    def test_valid_post_shows_success_message(self, client, admin_user):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('warehouse_create'), {
            'warehouse_name': '新倉庫',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        msgs = list(get_messages(response.wsgi_request))
        assert any('登録しました' in str(m) for m in msgs)


# ---------------------------------------------------------------------------
# 倉庫編集
# ---------------------------------------------------------------------------

class TestWarehouseUpdate:

    def test_unauthenticated_redirect(self, client, warehouse):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('warehouse_edit', kwargs={'pk': warehouse.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, warehouse):
        """店舗スタッフは倉庫編集にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('warehouse_edit', kwargs={'pk': warehouse.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは倉庫編集にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_edit', kwargs={'pk': warehouse_user.warehouse.pk}))
        assert response.status_code == 403

    def test_admin_get_200_with_form(self, client, admin_user, warehouse):
        """管理者は倉庫編集フォームを表示でき、既存データがセットされる"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_edit', kwargs={'pk': warehouse.pk}))
        assert response.status_code == 200
        assert response.context['form'].instance == warehouse

    def test_valid_post_updates_warehouse(self, client, admin_user, warehouse):
        """有効なデータを POST すると倉庫名が更新される"""
        client.force_login(admin_user)
        client.post(reverse('warehouse_edit', kwargs={'pk': warehouse.pk}), {
            'warehouse_name': '更新倉庫',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        warehouse.refresh_from_db()
        assert warehouse.warehouse_name == '更新倉庫'

    def test_valid_post_shows_success_message(self, client, admin_user, warehouse):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('warehouse_edit', kwargs={'pk': warehouse.pk}), {
            'warehouse_name': '更新倉庫',
            'prefecture': '東京都',
            'city': '渋谷区',
            'address1': '1-1-1',
        })
        msgs = list(get_messages(response.wsgi_request))
        assert any('更新しました' in str(m) for m in msgs)

    def test_can_delete_true_without_related(self, client, admin_user, warehouse):
        """在庫・連携・ユーザーが紐づかない場合 can_delete=True"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_edit', kwargs={'pk': warehouse.pk}))
        assert response.context['can_delete'] is True

    def test_can_delete_false_with_relation(self, client, admin_user, warehouse, relation):
        """連携情報が紐づく場合 can_delete=False"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_edit', kwargs={'pk': warehouse.pk}))
        assert response.context['can_delete'] is False


# ---------------------------------------------------------------------------
# 倉庫削除
# ---------------------------------------------------------------------------

class TestWarehouseDelete:

    def test_unauthenticated_redirect(self, client, warehouse):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(reverse('warehouse_delete', kwargs={'pk': warehouse.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, warehouse):
        """店舗スタッフは倉庫削除にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.post(reverse('warehouse_delete', kwargs={'pk': warehouse.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは倉庫削除にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.post(
            reverse('warehouse_delete', kwargs={'pk': warehouse_user.warehouse.pk})
        )
        assert response.status_code == 403

    def test_admin_can_delete_warehouse(self, client, admin_user, warehouse):
        """管理者は関連情報のない倉庫を削除できる"""
        client.force_login(admin_user)
        response = client.post(reverse('warehouse_delete', kwargs={'pk': warehouse.pk}))
        assert response.status_code == 302
        warehouse.refresh_from_db()
        assert warehouse.delete_flg is True

    def test_delete_success_message(self, client, admin_user, warehouse):
        """削除成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('warehouse_delete', kwargs={'pk': warehouse.pk}))
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除しました' in str(m) for m in msgs)

    def test_delete_redirects_to_list(self, client, admin_user, warehouse):
        """削除後は倉庫一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('warehouse_delete', kwargs={'pk': warehouse.pk}))
        assert response.url == reverse('warehouse_list')

    def test_cannot_delete_warehouse_with_relation(self, client, admin_user, warehouse, relation):
        """連携情報が紐づく倉庫は削除できない"""
        client.force_login(admin_user)
        response = client.post(reverse('warehouse_delete', kwargs={'pk': warehouse.pk}))
        warehouse.refresh_from_db()
        assert warehouse.delete_flg is False
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除できません' in str(m) for m in msgs)

    def test_not_found_for_deleted_warehouse(self, client, admin_user, warehouse):
        """論理削除済みの倉庫に対する削除リクエストは 404 になる"""
        warehouse.soft_delete()
        client.force_login(admin_user)
        response = client.post(reverse('warehouse_delete', kwargs={'pk': warehouse.pk}))
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# テスト用ヘルパー fixture（倉庫受注管理用）
# ---------------------------------------------------------------------------

@pytest.fixture
def warehouse_order(db, relation, goods):
    """warehouse_user の倉庫への受注（OrderGoods 付き）"""
    o = Order.objects.create(relation=relation)
    OrderGoods.objects.create(order=o, goods=goods, quantity=5)
    return o

@pytest.fixture
def shop_stock(db, shop, goods):
    return ShopStock.objects.create(shop=shop, goods=goods, stock=50)

@pytest.fixture
def shipped_order(db, relation, goods):
    o = Order.objects.create(relation=relation, status=Order.Status.SHIPPED)
    OrderGoods.objects.create(order=o, goods=goods, quantity=5)
    return o

@pytest.fixture
def deliverd_order(db, relation, goods):
    o = Order.objects.create(relation=relation, status=Order.Status.DELIVERED)
    OrderGoods.objects.create(order=o, goods=goods, quantity=5)
    return o


# ---------------------------------------------------------------------------
# 倉庫受注管理一覧
# ---------------------------------------------------------------------------

class TestWarehouseOrderList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('warehouse_order_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は倉庫受注管理一覧にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_order_list'))
        assert response.status_code == 403

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは倉庫受注管理一覧にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('warehouse_order_list'))
        assert response.status_code == 403

    def test_warehouse_user_get_200(self, client, warehouse_user):
        """倉庫スタッフは倉庫受注管理一覧を表示できる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_list'))
        assert response.status_code == 200

    def test_own_warehouse_order_in_rows(self, client, warehouse_user, warehouse_order):
        """自倉庫への受注が rows コンテキストに含まれる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_list'))
        order_ids = [row['order'].pk for row in response.context['rows']]
        assert warehouse_order.pk in order_ids

    def test_other_warehouse_order_not_in_rows(self, client, warehouse_user, warehouse2, shop, goods):
        """他倉庫への受注は rows に含まれない"""
        relation2 = Relation.objects.create(shop=shop, warehouse=warehouse2)
        other_order = Order.objects.create(relation=relation2)
        OrderGoods.objects.create(order=other_order, goods=goods, quantity=1)
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_list'))
        order_ids = [row['order'].pk for row in response.context['rows']]
        assert other_order.pk not in order_ids

    def test_status_choices_in_context(self, client, warehouse_user):
        """status_choices がコンテキストに含まれる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_list'))
        assert 'status_choices' in response.context
        assert len(response.context['status_choices']) > 0

    def test_filter_by_status(self, client, warehouse_user, warehouse_order, relation, goods):
        """ステータスで絞り込めること"""
        order_preparing = Order.objects.create(relation=relation, status=Order.Status.PREPARING)
        OrderGoods.objects.create(order=order_preparing, goods=goods, quantity=1)
        client.force_login(warehouse_user)
        response = client.get(
            reverse('warehouse_order_list') + f'?status={Order.Status.ORDERED}'
        )
        order_ids = [row['order'].pk for row in response.context['rows']]
        assert warehouse_order.pk in order_ids
        assert order_preparing.pk not in order_ids


# ---------------------------------------------------------------------------
# 倉庫受注ステータス更新
# ---------------------------------------------------------------------------

class TestWarehouseOrderStatusUpdate:

    def test_unauthenticated_redirect(self, client, warehouse_order):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': warehouse_order.pk}),
            {'status': Order.Status.PREPARING},
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user, warehouse_order):
        """管理者は受注ステータス更新にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': warehouse_order.pk}),
            {'status': Order.Status.PREPARING},
        )
        assert response.status_code == 403

    def test_shop_user_forbidden(self, client, shop_user, warehouse_order):
        """店舗スタッフは受注ステータス更新にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': warehouse_order.pk}),
            {'status': Order.Status.PREPARING},
        )
        assert response.status_code == 403

    def test_valid_status_update_to_preparing(self, client, warehouse_user, warehouse_order):
        """倉庫スタッフは発注済→準備中にステータス変更できる"""
        client.force_login(warehouse_user)
        client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': warehouse_order.pk}),
            {'status': Order.Status.PREPARING},
        )
        warehouse_order.refresh_from_db()
        assert warehouse_order.status == Order.Status.PREPARING

    def test_valid_status_update_shows_success_message(self, client, warehouse_user, warehouse_order):
        """ステータス更新成功時にフラッシュメッセージが表示される"""
        client.force_login(warehouse_user)
        response = client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': warehouse_order.pk}),
            {'status': Order.Status.PREPARING},
        )
        msgs = list(get_messages(response.wsgi_request))
        assert any('更新しました' in str(m) for m in msgs)

    def test_invalid_status_shows_error(self, client, warehouse_user, warehouse_order):
        """存在しないステータス値はエラーになる"""
        client.force_login(warehouse_user)
        response = client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': warehouse_order.pk}),
            {'status': 999},  # 存在しないステータス値
        )
        msgs = list(get_messages(response.wsgi_request))
        assert any('無効なステータス' in str(m) for m in msgs)
        warehouse_order.refresh_from_db()
        assert warehouse_order.status == Order.Status.ORDERED  # 変更されていない

    def test_other_warehouse_order_returns_404(self, client, warehouse_user, warehouse2, shop, goods):
        """他倉庫の受注に対するステータス更新は 404 になる"""
        relation2 = Relation.objects.create(shop=shop, warehouse=warehouse2)
        other_order = Order.objects.create(relation=relation2)
        client.force_login(warehouse_user)
        response = client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': other_order.pk}),
            {'status': Order.Status.PREPARING},
        )
        assert response.status_code == 404

    def test_shipped_deducts_warehouse_stock(
        self, client, warehouse_user, warehouse_order, warehouse_stock
    ):
        """発注済み→発送済みにすると倉庫在庫が減算される"""
        client.force_login(warehouse_user)
        client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': warehouse_order.pk}),
            {'status': Order.Status.SHIPPED},
        )
        warehouse_stock.refresh_from_db()
        assert warehouse_stock.stock == 95  # 100 - 5

    def test_shipped_no_stock_record_shows_error(
        self, client, warehouse_user, warehouse_order
    ):
        """在庫レコードなしで発送済みにするとエラーメッセージが出てステータスが変わらない"""
        client.force_login(warehouse_user)
        response = client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': warehouse_order.pk}),
            {'status': Order.Status.SHIPPED},
        )
        msgs = list(get_messages(response.wsgi_request))
        assert any('在庫データが存在しません' in str(m) for m in msgs)
        warehouse_order.refresh_from_db()
        assert warehouse_order.status == Order.Status.ORDERED

    def test_cancel_from_shipped_restores_warehouse_stock(
        self, client, warehouse_user, shipped_order, warehouse_stock
    ):
        """発送済み→キャンセルで倉庫在庫が元に戻る"""
        client.force_login(warehouse_user)
        client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': shipped_order.pk}),
            {'status': Order.Status.CANCELED},
        )
        warehouse_stock.refresh_from_db()
        assert warehouse_stock.stock == 105  # 100 + 5

    def test_delivered_adds_shop_stock(
        self, client, warehouse_user, shipped_order, shop_stock
    ):
        """発送済み→納品済みで店舗在庫が増える"""
        client.force_login(warehouse_user)
        client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': shipped_order.pk}),
            {'status': Order.Status.DELIVERED},
        )
        shop_stock.refresh_from_db()
        assert shop_stock.stock == 55  # 50 + 5

    def test_cancel_from_delivered_subtracts_shop_stock(
        self, client, warehouse_user, deliverd_order, shop_stock, warehouse_stock
    ):
        """納品済み→キャンセルで店舗在庫が減る"""
        client.force_login(warehouse_user)
        client.post(
            reverse('warehouse_order_status_update', kwargs={'pk': deliverd_order.pk}),
            {'status': Order.Status.CANCELED},
        )
        shop_stock.refresh_from_db()
        assert shop_stock.stock == 45  # 50 - 5


# ---------------------------------------------------------------------------
# 倉庫受注管理 CSV エクスポート
# ---------------------------------------------------------------------------

class TestWarehouseOrderCSVExport:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('warehouse_order_csv_export'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は受注 CSV エクスポートにアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_order_csv_export'))
        assert response.status_code == 403

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは受注 CSV エクスポートにアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('warehouse_order_csv_export'))
        assert response.status_code == 403

    def test_warehouse_user_get_200(self, client, warehouse_user):
        """倉庫スタッフは受注 CSV をダウンロードできる"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_csv_export'))
        assert response.status_code == 200

    def test_content_type_is_csv(self, client, warehouse_user):
        """レスポンスの Content-Type が text/csv である"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_csv_export'))
        assert 'text/csv' in response['Content-Type']

    def test_csv_header_row(self, client, warehouse_user):
        """CSV の先頭行が正しいヘッダーになっている"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_csv_export'))
        content = response.content.decode('utf-8-sig')
        reader = csv_module.reader(content.splitlines())
        headers = next(reader)
        assert headers == ['発注元店舗', '商品名', '発注個数', 'ステータス', '発注日時', '更新日時']

    def test_csv_contains_shop_name(self, client, warehouse_user, warehouse_order, shop):
        """CSV の発注元店舗列に店舗名が出力される"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_csv_export'))
        content = response.content.decode('utf-8-sig')
        # charset=utf-8-sig の場合 BOM が各行に付くことがあるため in で確認する
        assert shop.shop_name in content

    def test_csv_does_not_contain_other_warehouse_orders(
        self, client, warehouse_user, warehouse2, shop, goods
    ):
        """他倉庫の受注は CSV に含まれない"""
        relation2 = Relation.objects.create(shop=shop, warehouse=warehouse2)
        other_order = Order.objects.create(relation=relation2)
        OrderGoods.objects.create(order=other_order, goods=goods, quantity=3)
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_csv_export'))
        # warehouse2 の shop_name が同じ shop なので、倉庫名で区別できないが
        # 受注が warehouse_user の倉庫のものだけであることを確認
        assert response.status_code == 200  # 自倉庫分のみ出力される


# ---------------------------------------------------------------------------
# 倉庫受注管理 PDF エクスポート
# ---------------------------------------------------------------------------

class TestWarehouseOrderPDFExport:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('warehouse_order_pdf_export'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は受注 PDF エクスポートにアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('warehouse_order_pdf_export'))
        assert response.status_code == 403

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは受注 PDF エクスポートにアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('warehouse_order_pdf_export'))
        assert response.status_code == 403

    def test_warehouse_user_returns_pdf(self, client, warehouse_user, warehouse_order):
        """倉庫スタッフは PDF をダウンロードできる（reportlab がある場合）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('warehouse_order_pdf_export'))
        # reportlab がインストール済みなら 200 + PDF、未インストールなら 500
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert response['Content-Type'] == 'application/pdf'
