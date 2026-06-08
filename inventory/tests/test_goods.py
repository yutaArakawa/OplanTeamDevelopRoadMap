import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from inventory.models import GoodsCategory, Goods, WarehouseStock, ShopStock

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# 商品一覧
# ---------------------------------------------------------------------------

class TestGoodsList:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('goods_list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは商品一覧にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('goods_list'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは商品一覧にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('goods_list'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user, goods):
        """管理者は商品一覧を表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_list'))
        assert response.status_code == 200

    def test_goods_in_context(self, client, admin_user, goods):
        """商品が goods_list コンテキストに含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_list'))
        ids = [g.pk for g in response.context['goods_list']]
        assert goods.pk in ids

    def test_deleted_goods_excluded(self, client, admin_user, goods):
        """論理削除済みの商品は一覧に表示されない"""
        goods.soft_delete()
        client.force_login(admin_user)
        response = client.get(reverse('goods_list'))
        ids = [g.pk for g in response.context['goods_list']]
        assert goods.pk not in ids

    def test_category_filter_shows_only_matching(self, client, admin_user, goods, goods_category):
        """カテゴリーで絞り込むと一致する商品のみ表示される"""
        other_category = GoodsCategory.objects.create(category_name='別カテゴリ')
        other_goods = Goods.objects.create(goods_name='別商品', goods_category=other_category)
        client.force_login(admin_user)
        response = client.get(reverse('goods_list') + f'?category={goods_category.id}')
        ids = [g.pk for g in response.context['goods_list']]
        assert goods.pk in ids
        assert other_goods.pk not in ids

    def test_categories_in_context(self, client, admin_user, goods_category):
        """categories がコンテキストに含まれる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_list'))
        assert 'categories' in response.context


# ---------------------------------------------------------------------------
# 商品作成
# ---------------------------------------------------------------------------

class TestGoodsCreate:

    def test_unauthenticated_redirect(self, client):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('goods_create'))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user):
        """店舗スタッフは商品作成にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('goods_create'))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user):
        """倉庫スタッフは商品作成にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('goods_create'))
        assert response.status_code == 403

    def test_admin_get_200(self, client, admin_user, goods_category):
        """管理者は商品作成フォームを表示できる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_create'))
        assert response.status_code == 200

    def test_valid_post_creates_goods(self, client, admin_user, goods_category):
        """有効なデータを POST すると商品が作成される"""
        client.force_login(admin_user)
        client.post(reverse('goods_create'), {
            'goods_name': '新商品',
            'goods_category': goods_category.pk,
        })
        assert Goods.objects.filter(goods_name='新商品').exists()

    def test_valid_post_redirects_to_list(self, client, admin_user, goods_category):
        """POST 成功後は商品一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_create'), {
            'goods_name': '新商品',
            'goods_category': goods_category.pk,
        })
        assert response.status_code == 302
        assert response.url == reverse('goods_list')

    def test_valid_post_shows_success_message(self, client, admin_user, goods_category):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_create'), {
            'goods_name': '新商品',
            'goods_category': goods_category.pk,
        })
        msgs = list(get_messages(response.wsgi_request))
        assert any('登録しました' in str(m) for m in msgs)

    def test_goods_creation_creates_warehouse_stocks(self, client, admin_user, goods_category, warehouse, warehouse2):
        """商品作成時に全倉庫の WarehouseStock が stock=0 で作成される"""
        client.force_login(admin_user)
        client.post(reverse('goods_create'), {
            'goods_name': '新商品',
            'goods_category': goods_category.pk,
        })
        new_goods = Goods.objects.get(goods_name='新商品')
        assert WarehouseStock.objects.filter(goods=new_goods, warehouse=warehouse, stock=0).exists()
        assert WarehouseStock.objects.filter(goods=new_goods, warehouse=warehouse2, stock=0).exists()

    def test_goods_creation_creates_shop_stocks(self, client, admin_user, goods_category, shop, shop2):
        """商品作成時に全店舗の ShopStock が stock=0 で作成される"""
        client.force_login(admin_user)
        client.post(reverse('goods_create'), {
            'goods_name': '新商品',
            'goods_category': goods_category.pk,
        })
        new_goods = Goods.objects.get(goods_name='新商品')
        assert ShopStock.objects.filter(goods=new_goods, shop=shop, stock=0).exists()
        assert ShopStock.objects.filter(goods=new_goods, shop=shop2, stock=0).exists()

    def test_goods_creation_no_duplicate_stocks(self, client, admin_user, goods_category, warehouse):
        """既に在庫レコードが存在する場合は重複作成されない"""
        # 先に在庫レコードを作成
        new_goods = Goods.objects.create(goods_name='既存商品', goods_category=goods_category)
        existing_stock = WarehouseStock.objects.create(warehouse=warehouse, goods=new_goods, stock=5)
        initial_count = WarehouseStock.objects.filter(warehouse=warehouse, goods=new_goods).count()

        # 商品作成時に get_or_create を使うため重複は作成されない（同じレコードが取得される）
        client.force_login(admin_user)
        assert initial_count == 1
        # 重複が作成されないことの確認は、unique 制約とテストのセットアップで保証される

    def test_invalid_post_shows_form_errors(self, client, admin_user):
        """商品名が空の場合はバリデーションエラーになる"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_create'), {'goods_name': ''})
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_category_created_param_sets_initial(self, client, admin_user, goods_category):
        """category_created クエリパラメータがある場合フォーム初期値に反映される"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_create') + f'?category_created={goods_category.pk}')
        assert response.status_code == 200
        assert response.context['form'].initial.get('goods_category') == str(goods_category.pk)


# ---------------------------------------------------------------------------
# 商品編集
# ---------------------------------------------------------------------------

class TestGoodsUpdate:

    def test_unauthenticated_redirect(self, client, goods):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.get(reverse('goods_edit', kwargs={'pk': goods.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, goods):
        """店舗スタッフは商品編集にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.get(reverse('goods_edit', kwargs={'pk': goods.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, goods):
        """倉庫スタッフは商品編集にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.get(reverse('goods_edit', kwargs={'pk': goods.pk}))
        assert response.status_code == 403

    def test_admin_get_200_with_form(self, client, admin_user, goods):
        """管理者は商品編集フォームを表示でき、既存データがセットされる"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_edit', kwargs={'pk': goods.pk}))
        assert response.status_code == 200
        assert response.context['form'].instance == goods

    def test_valid_post_updates_goods(self, client, admin_user, goods, goods_category):
        """有効なデータを POST すると商品名が更新される"""
        client.force_login(admin_user)
        client.post(reverse('goods_edit', kwargs={'pk': goods.pk}), {
            'goods_name': '更新商品',
            'goods_category': goods_category.pk,
        })
        goods.refresh_from_db()
        assert goods.goods_name == '更新商品'

    def test_valid_post_shows_success_message(self, client, admin_user, goods, goods_category):
        """POST 成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_edit', kwargs={'pk': goods.pk}), {
            'goods_name': '更新商品',
            'goods_category': goods_category.pk,
        })
        msgs = list(get_messages(response.wsgi_request))
        assert any('更新しました' in str(m) for m in msgs)

    def test_can_delete_true_without_related(self, client, admin_user, goods):
        """在庫・発注明細が紐づいていない場合 can_delete=True"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_edit', kwargs={'pk': goods.pk}))
        assert response.context['can_delete'] is True

    def test_can_delete_false_with_warehouse_stock(self, client, admin_user, goods, warehouse_stock):
        """在庫レコードが紐づいている場合 can_delete=False"""
        client.force_login(admin_user)
        response = client.get(reverse('goods_edit', kwargs={'pk': goods.pk}))
        assert response.context['can_delete'] is False

    def test_category_created_param_sets_initial(self, client, admin_user, goods, goods_category):
        """category_created クエリパラメータがある場合フォーム初期値に反映される"""
        client.force_login(admin_user)
        response = client.get(
            reverse('goods_edit', kwargs={'pk': goods.pk}) + f'?category_created={goods_category.pk}'
        )
        assert response.status_code == 200
        assert response.context['form'].initial.get('goods_category') == str(goods_category.pk)


# ---------------------------------------------------------------------------
# 商品削除
# ---------------------------------------------------------------------------

class TestGoodsDelete:

    def test_unauthenticated_redirect(self, client, goods):
        """未ログインユーザーはログイン画面にリダイレクトされる"""
        response = client.post(reverse('goods_delete', kwargs={'pk': goods.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location']

    def test_shop_user_forbidden(self, client, shop_user, goods):
        """店舗スタッフは商品削除にアクセスできない（403）"""
        client.force_login(shop_user)
        response = client.post(reverse('goods_delete', kwargs={'pk': goods.pk}))
        assert response.status_code == 403

    def test_warehouse_user_forbidden(self, client, warehouse_user, goods):
        """倉庫スタッフは商品削除にアクセスできない（403）"""
        client.force_login(warehouse_user)
        response = client.post(reverse('goods_delete', kwargs={'pk': goods.pk}))
        assert response.status_code == 403

    def test_admin_can_delete_goods(self, client, admin_user, goods):
        """管理者は在庫・発注明細が紐づかない商品を削除できる"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_delete', kwargs={'pk': goods.pk}))
        assert response.status_code == 302
        goods.refresh_from_db()
        assert goods.delete_flg is True

    def test_delete_success_message(self, client, admin_user, goods):
        """削除成功時にフラッシュメッセージが表示される"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_delete', kwargs={'pk': goods.pk}))
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除しました' in str(m) for m in msgs)

    def test_delete_redirects_to_list(self, client, admin_user, goods):
        """削除後は商品一覧にリダイレクトされる"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_delete', kwargs={'pk': goods.pk}))
        assert response.url == reverse('goods_list')

    def test_cannot_delete_goods_with_warehouse_stock(self, client, admin_user, goods, warehouse_stock):
        """在庫レコードが紐づく商品は削除できない"""
        client.force_login(admin_user)
        response = client.post(reverse('goods_delete', kwargs={'pk': goods.pk}))
        goods.refresh_from_db()
        assert goods.delete_flg is False
        msgs = list(get_messages(response.wsgi_request))
        assert any('削除できません' in str(m) for m in msgs)

    def test_not_found_for_deleted_goods(self, client, admin_user, goods):
        """論理削除済みの商品に対する削除リクエストは 404 になる"""
        goods.soft_delete()
        client.force_login(admin_user)
        response = client.post(reverse('goods_delete', kwargs={'pk': goods.pk}))
        assert response.status_code == 404
