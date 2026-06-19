from accounts.models import User
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
    # 想定していない権限の場合は空を返す
    return User.active_objects.none()
