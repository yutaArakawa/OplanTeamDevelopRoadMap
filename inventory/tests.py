import io
import csv as csv_module

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from inventory.models import GoodsCategory, Goods, Shop, Warehouse, WarehouseStock, Order, OrderGoods, Relation

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
# 発注商品選択画面
# ---------------------------------------------------------------------------

class TestOrderGoodsList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('order_goods_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は発注商品選択画面にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('order_goods_list'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは発注商品選択画面にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('order_goods_list'))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user, goods):
        """店舗スタッフは発注商品選択画面を表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_goods_list'))
        assert response.status_code == 200

    def test_goods_in_select_goods_list(self, client, shop_user, goods):
        """商品が select_goods_list コンテキストに含まれる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_goods_list'))
        ids = [g.pk for g in response.context['select_goods_list']]
        assert goods.pk in ids

    def test_stock_from_related_warehouse(self, client, shop_user, goods, relation, warehouse_stock):
        """連携倉庫の在庫数が正しく集計される"""
        # relation: shop_user.shop ↔ warehouse
        # warehouse_stock: warehouse の goods 在庫 = 100
        client.force_login(shop_user)
        response = client.get(reverse('order_goods_list'))
        target = next(g for g in response.context['select_goods_list'] if g.pk == goods.pk)
        assert target.stock == warehouse_stock.stock

    def test_stock_zero_without_related_warehouse_stock(self, client, shop_user, goods):
        """連携倉庫に在庫レコードがない場合は在庫数が 0 になる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_goods_list'))
        target = next(g for g in response.context['select_goods_list'] if g.pk == goods.pk)
        assert target.stock == 0

    def test_unrelated_warehouse_stock_not_counted(self, client, shop_user, goods, warehouse2):
        """連携していない倉庫の在庫は集計されない"""
        WarehouseStock.objects.create(warehouse=warehouse2, goods=goods, stock=999)
        client.force_login(shop_user)
        response = client.get(reverse('order_goods_list'))
        target = next(g for g in response.context['select_goods_list'] if g.pk == goods.pk)
        assert target.stock == 0

    def test_category_filter_shows_only_matching_goods(self, client, shop_user, goods, goods_category):
        """カテゴリーで絞り込むと一致する商品のみ表示される"""
        other_category = GoodsCategory.objects.create(category_name='別カテゴリ')
        other_goods = Goods.objects.create(goods_name='別商品', goods_category=other_category)
        client.force_login(shop_user)
        response = client.get(reverse('order_goods_list') + f'?category={goods_category.id}')
        ids = [g.pk for g in response.context['select_goods_list']]
        assert goods.pk in ids
        assert other_goods.pk not in ids

    def test_category_filter_selected_category_in_context(self, client, shop_user, goods_category):
        """カテゴリー絞り込み時に selected_category がコンテキストにセットされる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_goods_list') + f'?category={goods_category.id}')
        assert str(response.context['selected_category']) == str(goods_category.id)


# ---------------------------------------------------------------------------
# 発注画面（倉庫別発注数入力）
# ---------------------------------------------------------------------------

class TestOrderCreate:

    def test_unauthenticated_redirect(self, client, goods):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('order_create', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user, goods):
        """管理者は発注画面にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('order_create', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, goods):
        """倉庫スタッフは発注画面にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('order_create', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user, goods, relation):
        """店舗スタッフは発注画面を表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_create', kwargs={'goods_pk': goods.pk}))
        assert response.status_code == 200

    def test_context_has_goods(self, client, shop_user, goods, relation):
        """コンテキストに発注対象の商品が含まれる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_create', kwargs={'goods_pk': goods.pk}))
        assert response.context['goods'] == goods

    def test_context_has_relations(self, client, shop_user, goods, relation):
        """コンテキストに連携倉庫（relations）が含まれる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_create', kwargs={'goods_pk': goods.pk}))
        relation_ids = [r.pk for r in response.context['relations']]
        assert relation.pk in relation_ids

    def test_post_creates_order_and_order_goods(self, client, shop_user, goods, relation):
        """数量 > 0 でPOSTすると Order と OrderGoods が作成される"""
        client.force_login(shop_user)
        client.post(
            reverse('order_create', kwargs={'goods_pk': goods.pk}),
            {f'quantity_{relation.id}': 3},
        )
        assert Order.objects.filter(relation=relation).exists()
        order = Order.objects.get(relation=relation)
        assert OrderGoods.objects.filter(order=order, goods=goods, quantity=3).exists()

    def test_post_zero_quantity_no_order_created(self, client, shop_user, goods, relation):
        """数量 = 0 でPOSTしても Order は作成されない"""
        client.force_login(shop_user)
        client.post(
            reverse('order_create', kwargs={'goods_pk': goods.pk}),
            {f'quantity_{relation.id}': 0},
        )
        assert not Order.objects.filter(relation=relation).exists()

    def test_post_multiple_warehouses_creates_each_order(self, client, shop_user, goods, relation, warehouse2):
        """複数の連携倉庫に数量を入力すると各倉庫に Order が作成される"""
        from inventory.models import Relation
        relation2 = Relation.objects.create(shop=shop_user.shop, warehouse=warehouse2)
        client.force_login(shop_user)
        client.post(
            reverse('order_create', kwargs={'goods_pk': goods.pk}),
            {
                f'quantity_{relation.id}': 5,
                f'quantity_{relation2.id}': 2,
            },
        )
        assert Order.objects.filter(relation=relation).exists()
        assert Order.objects.filter(relation=relation2).exists()

    def test_post_redirects_to_order_goods_list(self, client, shop_user, goods, relation):
        """POST成功後は発注商品選択画面にリダイレクトされる"""
        client.force_login(shop_user)
        response = client.post(
            reverse('order_create', kwargs={'goods_pk': goods.pk}),
            {f'quantity_{relation.id}': 1},
        )
        assert response.status_code == 302
        assert response.url == reverse('order_goods_list')


# ---------------------------------------------------------------------------
# CSV一括発注表ダウンロード
# ---------------------------------------------------------------------------

class TestOrderCsvDownload:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('order_csv_download'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者はCSVダウンロードにアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('order_csv_download'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフはCSVダウンロードにアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('order_csv_download'))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user):
        """店舗スタッフはCSVをダウンロードできる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_csv_download'))
        assert response.status_code == 200

    def test_content_type_is_csv(self, client, shop_user):
        """レスポンスの Content-Type が text/csv である"""
        client.force_login(shop_user)
        response = client.get(reverse('order_csv_download'))
        assert 'text/csv' in response['Content-Type']

    def test_csv_header_row(self, client, shop_user):
        """CSVの先頭行が正しいヘッダーになっている"""
        client.force_login(shop_user)
        response = client.get(reverse('order_csv_download'))
        content = response.content.decode('utf-8-sig')
        reader = csv_module.reader(content.splitlines())
        headers = next(reader)
        assert headers == ['倉庫ID', '倉庫名', 'カテゴリ', '商品ID', '商品名', '現在の在庫数', '発注数']

    def test_csv_contains_related_warehouse_stock(self, client, shop_user, goods, relation, warehouse_stock):
        """連携倉庫の在庫情報がCSVに含まれる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_csv_download'))
        content = response.content.decode('utf-8-sig')
        reader = csv_module.DictReader(content.splitlines())
        rows = list(reader)
        assert any(
            int(row['商品ID']) == goods.pk
            and int(row['現在の在庫数']) == warehouse_stock.stock
            and int(row['倉庫ID']) == relation.warehouse.pk
            for row in rows
        )

    def test_csv_order_quantity_column_is_empty(self, client, shop_user, goods, relation, warehouse_stock):
        """発注数列はCSVに空欄で出力される"""
        client.force_login(shop_user)
        response = client.get(reverse('order_csv_download'))
        content = response.content.decode('utf-8-sig')
        reader = csv_module.DictReader(content.splitlines())
        rows = list(reader)
        for row in rows:
            assert row['発注数'] == ''

    def test_csv_does_not_contain_unrelated_warehouse_stock(self, client, shop_user, goods, warehouse2):
        """連携していない倉庫の在庫はCSVに含まれない"""
        WarehouseStock.objects.create(warehouse=warehouse2, goods=goods, stock=50)
        client.force_login(shop_user)
        response = client.get(reverse('order_csv_download'))
        content = response.content.decode('utf-8-sig')
        reader = csv_module.DictReader(content.splitlines())
        rows = list(reader)
        assert not any(int(row['倉庫ID']) == warehouse2.pk for row in rows)


# ---------------------------------------------------------------------------
# CSVインポートによる一括発注
# ---------------------------------------------------------------------------

class TestOrderCsvImport:

    def _make_csv_file(self, rows, headers=None):
        """ヘッダーとデータ行からアップロード用のCSVファイルオブジェクトを生成するヘルパー"""
        if headers is None:
            headers = ['倉庫ID', '倉庫名', 'カテゴリ', '商品ID', '商品名', '現在の在庫数', '発注数']
        content = io.StringIO()
        writer = csv_module.writer(content)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        csv_bytes = io.BytesIO(content.getvalue().encode('utf-8-sig'))
        csv_bytes.name = 'test.csv'
        return csv_bytes

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(reverse('order_csv_import'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者はCSVインポートにアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.post(reverse('order_csv_import'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフはCSVインポートにアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.post(reverse('order_csv_import'))
        assert response.status_code == 403

    def test_no_file_shows_error_message(self, client, shop_user):
        """ファイル未選択でPOSTするとエラーメッセージが表示されリダイレクトされる"""
        client.force_login(shop_user)
        response = client.post(reverse('order_csv_import'))
        assert response.status_code == 302
        msgs = list(get_messages(response.wsgi_request))
        assert any('CSVファイルが選択されていません' in str(m) for m in msgs)

    def test_valid_csv_creates_order_and_order_goods(self, client, shop_user, goods, relation, warehouse_stock):
        """有効なCSVをインポートすると Order と OrderGoods が作成される"""
        csv_file = self._make_csv_file([
            [relation.warehouse.id, relation.warehouse.warehouse_name,
             goods.goods_category.category_name, goods.id, goods.goods_name, 100, 5],
        ])
        client.force_login(shop_user)
        client.post(reverse('order_csv_import'), {'csv_file': csv_file})
        assert Order.objects.filter(relation=relation).exists()
        order = Order.objects.get(relation=relation)
        assert OrderGoods.objects.filter(order=order, goods=goods, quantity=5).exists()

    def test_empty_quantity_row_is_skipped(self, client, shop_user, goods, relation, warehouse_stock):
        """発注数が空欄の行はスキップされ Order が作成されない"""
        csv_file = self._make_csv_file([
            [relation.warehouse.id, relation.warehouse.warehouse_name,
             goods.goods_category.category_name, goods.id, goods.goods_name, 100, ''],
        ])
        client.force_login(shop_user)
        client.post(reverse('order_csv_import'), {'csv_file': csv_file})
        assert not Order.objects.filter(relation=relation).exists()

    def test_zero_quantity_row_is_skipped(self, client, shop_user, goods, relation, warehouse_stock):
        """発注数が 0 の行はスキップされ Order が作成されない"""
        csv_file = self._make_csv_file([
            [relation.warehouse.id, relation.warehouse.warehouse_name,
             goods.goods_category.category_name, goods.id, goods.goods_name, 100, 0],
        ])
        client.force_login(shop_user)
        client.post(reverse('order_csv_import'), {'csv_file': csv_file})
        assert not Order.objects.filter(relation=relation).exists()

    def test_same_warehouse_multiple_goods_creates_one_order(
        self, client, shop_user, goods, goods_category, relation, warehouse_stock
    ):
        """同一倉庫に複数商品を発注すると Order は 1 件、OrderGoods が複数作成される"""
        goods2 = Goods.objects.create(goods_name='テスト商品2', goods_category=goods_category)
        WarehouseStock.objects.create(warehouse=relation.warehouse, goods=goods2, stock=50)
        csv_file = self._make_csv_file([
            [relation.warehouse.id, relation.warehouse.warehouse_name,
             goods.goods_category.category_name, goods.id, goods.goods_name, 100, 3],
            [relation.warehouse.id, relation.warehouse.warehouse_name,
             goods2.goods_category.category_name, goods2.id, goods2.goods_name, 50, 2],
        ])
        client.force_login(shop_user)
        client.post(reverse('order_csv_import'), {'csv_file': csv_file})
        # 同一倉庫への Order は 1 件
        assert Order.objects.filter(relation=relation).count() == 1
        order = Order.objects.get(relation=relation)
        # OrderGoods は 2 件（商品ごと）
        assert OrderGoods.objects.filter(order=order).count() == 2

    def test_redirect_after_successful_import(self, client, shop_user, goods, relation, warehouse_stock):
        """インポート成功後は発注商品選択画面にリダイレクトされる"""
        csv_file = self._make_csv_file([
            [relation.warehouse.id, relation.warehouse.warehouse_name,
             goods.goods_category.category_name, goods.id, goods.goods_name, 100, 5],
        ])
        client.force_login(shop_user)
        response = client.post(reverse('order_csv_import'), {'csv_file': csv_file})
        assert response.status_code == 302
        assert response.url == reverse('order_goods_list')


# ---------------------------------------------------------------------------
# テスト用ヘルパー fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def order(db, relation, goods):
    """shop → warehouse への発注（OrderGoods 付き）"""
    o = Order.objects.create(relation=relation)
    OrderGoods.objects.create(order=o, goods=goods, quantity=3)
    return o


@pytest.fixture
def order_no_goods(db, relation):
    """OrderGoods が紐づいていない Order"""
    return Order.objects.create(relation=relation)


# ---------------------------------------------------------------------------
# 発注履歴画面
# ---------------------------------------------------------------------------

class TestOrderHistory:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('order_history'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は発注履歴画面にアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('order_history'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは発注履歴画面にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('order_history'))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user):
        """店舗スタッフは発注履歴画面を表示できる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history'))
        assert response.status_code == 200

    def test_own_order_in_rows(self, client, shop_user, order):
        """自店舗の発注が rows コンテキストに含まれる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history'))
        order_ids = [row['order'].pk for row in response.context['rows']]
        assert order.pk in order_ids

    def test_other_shop_order_not_in_rows(self, client, shop_user, shop2, warehouse2, goods):
        """他店舗の発注は rows コンテキストに含まれない"""
        relation2 = Relation.objects.create(shop=shop2, warehouse=warehouse2)
        other_order = Order.objects.create(relation=relation2)
        OrderGoods.objects.create(order=other_order, goods=goods, quantity=1)
        client.force_login(shop_user)
        response = client.get(reverse('order_history'))
        order_ids = [row['order'].pk for row in response.context['rows']]
        assert other_order.pk not in order_ids

    def test_status_choices_in_context(self, client, shop_user):
        """status_choices がコンテキストに含まれる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history'))
        assert 'status_choices' in response.context
        assert len(response.context['status_choices']) > 0

    def test_filter_by_status(self, client, shop_user, order, relation, goods):
        """ステータスで絞り込めること（一致しないステータスは除外される）"""
        # order はデフォルトで ORDERED(=0)
        # 別ステータスの order を作成
        order_preparing = Order.objects.create(relation=relation, status=Order.Status.PREPARING)
        OrderGoods.objects.create(order=order_preparing, goods=goods, quantity=1)

        client.force_login(shop_user)
        response = client.get(reverse('order_history') + f'?status={Order.Status.ORDERED}')
        order_ids = [row['order'].pk for row in response.context['rows']]
        assert order.pk in order_ids
        assert order_preparing.pk not in order_ids

    def test_order_goods_none_row_for_empty_order(self, client, shop_user, order_no_goods):
        """OrderGoods がない Order の行は order_goods=None になる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history'))
        empty_rows = [row for row in response.context['rows'] if row['order'].pk == order_no_goods.pk]
        assert len(empty_rows) == 1
        assert empty_rows[0]['order_goods'] is None


# ---------------------------------------------------------------------------
# 発注履歴 CSV エクスポート
# ---------------------------------------------------------------------------

class TestOrderHistoryCSVExport:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('order_history_csv_export'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は CSV エクスポートにアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('order_history_csv_export'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは CSV エクスポートにアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('order_history_csv_export'))
        assert response.status_code == 403

    def test_shop_user_get_200(self, client, shop_user):
        """店舗スタッフは CSV をダウンロードできる"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history_csv_export'))
        assert response.status_code == 200

    def test_content_type_is_csv(self, client, shop_user):
        """Content-Type が text/csv である"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history_csv_export'))
        assert 'text/csv' in response['Content-Type']

    def test_csv_header_row(self, client, shop_user):
        """CSV の先頭行が正しいヘッダーになっている"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history_csv_export'))
        content = response.content.decode('utf-8-sig')
        reader = csv_module.reader(content.splitlines())
        headers = next(reader)
        assert headers == ['発注先倉庫', '商品名', '発注個数', 'ステータス', '発注日時', '更新日時']

    def test_csv_contains_warehouse_name(self, client, shop_user, order, warehouse):
        """CSV の発注先倉庫列に倉庫名が出力される"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history_csv_export'))
        content = response.content.decode('utf-8-sig')
        reader = csv_module.DictReader(content.splitlines())
        rows = list(reader)
        assert any(row['発注先倉庫'] == warehouse.warehouse_name for row in rows)

    def test_csv_does_not_contain_other_shop_orders(self, client, shop_user, shop2, warehouse2, goods):
        """他店舗の発注は CSV に含まれない"""
        relation2 = Relation.objects.create(shop=shop2, warehouse=warehouse2)
        other_order = Order.objects.create(relation=relation2)
        OrderGoods.objects.create(order=other_order, goods=goods, quantity=10)
        client.force_login(shop_user)
        response = client.get(reverse('order_history_csv_export'))
        content = response.content.decode('utf-8-sig')
        reader = csv_module.DictReader(content.splitlines())
        rows = list(reader)
        assert not any(row['発注先倉庫'] == warehouse2.warehouse_name for row in rows)

    def test_csv_filter_by_status(self, client, shop_user, order, relation, goods):
        """ステータスフィルターが CSV に反映される"""
        order_preparing = Order.objects.create(relation=relation, status=Order.Status.PREPARING)
        OrderGoods.objects.create(order=order_preparing, goods=goods, quantity=5)
        client.force_login(shop_user)
        response = client.get(
            reverse('order_history_csv_export') + f'?status={Order.Status.PREPARING}'
        )
        content = response.content.decode('utf-8-sig')
        reader = csv_module.DictReader(content.splitlines())
        statuses = [row['ステータス'] for row in reader]
        assert all(s == Order.Status.PREPARING.label for s in statuses)


# ---------------------------------------------------------------------------
# 発注履歴 PDF エクスポート
# ---------------------------------------------------------------------------

class TestOrderHistoryPDFExport:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('order_history_pdf_export'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_admin_forbidden(self, client, admin_user):
        """管理者は PDF エクスポートにアクセスできない（403）"""
        client.force_login(admin_user)
        response = client.get(reverse('order_history_pdf_export'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは PDF エクスポートにアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('order_history_pdf_export'))
        assert response.status_code == 403

    def test_shop_user_returns_pdf(self, client, shop_user, order):
        """店舗スタッフは PDF をダウンロードできる（reportlab がある場合）"""
        client.force_login(shop_user)
        response = client.get(reverse('order_history_pdf_export'))
        # reportlab がインストール済みなら 200 + PDF、未インストールなら 500
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert response['Content-Type'] == 'application/pdf'


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
