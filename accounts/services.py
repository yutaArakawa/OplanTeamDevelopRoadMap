from django.db import transaction
from accounts.models import User, Authority
from inventory.models import Shop, Warehouse
from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE


def getUserList(authority, affiliation=None):
    query_map = {
        AUTHORITY_ADMIN: lambda: User.active_objects.all(),
        AUTHORITY_SHOP: lambda: User.active_objects.filter(authority=authority, shop=affiliation),
        AUTHORITY_WAREHOUSE: lambda: User.active_objects.filter(authority=authority, warehouse=affiliation),
    }

    query = query_map.get(authority)
    if query:
        return query()
    return User.active_objects.none()


def getFormOptions(login_user):
    """作成・編集フォームの選択肢を返す（権限・店舗・倉庫）"""
    if login_user.authority_id == AUTHORITY_ADMIN:
        authorities = list(Authority.active_objects.values('id', 'authority_name'))
    elif login_user.authority_id == AUTHORITY_SHOP:
        authorities = list(Authority.active_objects.filter(id=AUTHORITY_SHOP).values('id', 'authority_name'))
    else:
        authorities = list(Authority.active_objects.filter(id=AUTHORITY_WAREHOUSE).values('id', 'authority_name'))

    shops = list(Shop.active_objects.order_by('shop_name').values('id', 'shop_name'))
    warehouses = list(Warehouse.active_objects.order_by('warehouse_name').values('id', 'warehouse_name'))
    return authorities, shops, warehouses


def getFilterOptions():
    """一覧フィルター用の選択肢を返す（管理者専用）"""
    authorities = list(Authority.objects.values('id', 'authority_name'))
    shops = list(Shop.active_objects.values('id', 'shop_name'))
    warehouses = list(Warehouse.active_objects.values('id', 'warehouse_name'))
    return authorities, shops, warehouses


def getUser(pk):
    """pkでユーザーを1件取得。存在しない場合はNoneを返す"""
    try:
        return User.active_objects.get(pk=pk)
    except User.DoesNotExist:
        return None


@transaction.atomic
def createUser(username, password, user_gender, authority_id, shop_id, warehouse_id):
    """ユーザーを作成して返す"""
    user = User(
        username=username,
        user_gender=int(user_gender),
        authority_id=int(authority_id),
        shop_id=int(shop_id) if shop_id else None,
        warehouse_id=int(warehouse_id) if warehouse_id else None,
    )
    user.set_password(password)
    user.save()
    return user


@transaction.atomic
def updateUser(user, password=None, **fields):
    """ユーザー情報を更新して保存する。fieldsに渡したキーのみ更新される"""
    for key, value in fields.items():
        setattr(user, key, value)
    if password:
        user.set_password(password)
    user.save()


@transaction.atomic
def deleteUser(user):
    """ユーザーを論理削除する"""
    user.delete_flg = True
    user.save()
