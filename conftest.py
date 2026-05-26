import pytest
from accounts.models import User, Authority
from inventory.models import GoodsCategory, Goods, Shop, Warehouse, WarehouseStock, Relation
from inquiry.models import Inquiry


@pytest.fixture
def authority_admin(db):
    # id を定数 AUTHORITY_ADMIN=1 に合わせる
    return Authority.objects.create(id=1, authority_name='管理者')


@pytest.fixture
def authority_shop(db):
    return Authority.objects.create(id=2, authority_name='店舗スタッフ')


@pytest.fixture
def authority_warehouse(db):
    return Authority.objects.create(id=3, authority_name='倉庫スタッフ')


@pytest.fixture
def shop(db):
    return Shop.objects.create(
        shop_name='テスト店舗',
        prefecture='東京都',
        city='渋谷区',
        address1='1-1-1',
    )


@pytest.fixture
def shop2(db):
    return Shop.objects.create(
        shop_name='テスト店舗2',
        prefecture='大阪府',
        city='大阪市',
        address1='2-2-2',
    )


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(
        warehouse_name='テスト倉庫',
        prefecture='東京都',
        city='渋谷区',
        address1='3-3-3',
    )


@pytest.fixture
def warehouse2(db):
    return Warehouse.objects.create(
        warehouse_name='テスト倉庫2',
        prefecture='大阪府',
        city='大阪市',
        address1='4-4-4',
    )


@pytest.fixture
def admin_user(db, authority_admin):
    return User.objects.create_user(
        username='admin_user',
        password='testpass123',
        user_gender=1,
        authority=authority_admin,
    )


@pytest.fixture
def shop_user(db, authority_shop, shop):
    return User.objects.create_user(
        username='shop_user',
        password='testpass123',
        user_gender=1,
        authority=authority_shop,
        shop=shop,
    )


@pytest.fixture
def warehouse_user(db, authority_warehouse, warehouse):
    return User.objects.create_user(
        username='warehouse_user',
        password='testpass123',
        user_gender=1,
        authority=authority_warehouse,
        warehouse=warehouse,
    )


@pytest.fixture
def deleted_user(db, authority_admin):
    user = User.objects.create_user(
        username='deleted_user',
        password='testpass123',
        user_gender=1,
        authority=authority_admin,
    )
    user.delete_flg = True
    user.save()
    return user


@pytest.fixture
def goods_category(db):
    return GoodsCategory.objects.create(category_name='テストカテゴリ')


@pytest.fixture
def goods(db, goods_category):
    return Goods.objects.create(goods_name='テスト商品', goods_category=goods_category)


@pytest.fixture
def warehouse_stock(db, warehouse_user, goods):
    return WarehouseStock.objects.create(
        warehouse=warehouse_user.warehouse,
        goods=goods,
        stock=100,
    )

@pytest.fixture
def relation(db, shop, warehouse):
    return Relation.objects.create(shop=shop, warehouse=warehouse)


@pytest.fixture
def inquiry_to_admin(db, authority_admin, shop_user):
    """店舗スタッフ → 管理者 宛の問い合わせ"""
    return Inquiry.objects.create(
        to_authority=authority_admin,
        from_user=shop_user,
        from_authority=shop_user.authority,
        from_belong_shop=shop_user.shop,
        inquiry_details='管理者宛のテスト問い合わせ',
    )


@pytest.fixture
def inquiry_to_shop(db, authority_shop, warehouse_user, relation):
    """倉庫スタッフ → 店舗スタッフ 宛の問い合わせ"""
    return Inquiry.objects.create(
        to_authority=authority_shop,
        from_user=warehouse_user,
        from_authority=warehouse_user.authority,
        from_belong_warehouse=warehouse_user.warehouse,
        to_relation=relation,
        inquiry_details='店舗スタッフ宛のテスト問い合わせ',
    )


@pytest.fixture
def inquiry_to_warehouse(db, authority_warehouse, shop_user, relation):
    """店舗スタッフ → 倉庫スタッフ 宛の問い合わせ"""
    return Inquiry.objects.create(
        to_authority=authority_warehouse,
        from_user=shop_user,
        from_authority=shop_user.authority,
        from_belong_shop=shop_user.shop,
        to_relation=relation,
        inquiry_details='倉庫スタッフ宛のテスト問い合わせ',
    )
