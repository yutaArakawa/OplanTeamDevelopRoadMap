import pytest
from django.urls import reverse
from inventory.models import GoodsCategory, Goods, WarehouseStock

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
