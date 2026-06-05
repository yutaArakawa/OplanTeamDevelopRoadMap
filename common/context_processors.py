from common.constants import (
    AUTHORITY_ADMIN,
    AUTHORITY_SHOP,
    AUTHORITY_WAREHOUSE,
    GENDER_MEN,
    GENDER_WOMEN,
    GENDER_OTHERS,
)

def authority_constants(request):
    return {
        'AUTHORITY_ADMIN'     : AUTHORITY_ADMIN,
        'AUTHORITY_SHOP'      : AUTHORITY_SHOP,
        'AUTHORITY_WAREHOUSE' : AUTHORITY_WAREHOUSE,
        'GENDER_MEN'          : GENDER_MEN,
        'GENDER_WOMEN'        : GENDER_WOMEN,
        'GENDER_OTHERS'       : GENDER_OTHERS,
    }