import re
from django.core.exceptions import ValidationError
from accounts.models import User
from common.constants import AUTHORITY_SHOP, AUTHORITY_WAREHOUSE


class CustomPasswordValidator:

    def validate(self, password, user=None):
        if not re.match(r'^[a-zA-Z0-9]+$', password):
            raise ValidationError('パスワードは半角英数字のみ使用できます')

    def get_help_text(self):
        return 'パスワードは半角英数字のみ使用できます'


def validate_user_fields(username, user_gender, authority, shop_id, warehouse_id, exclude_pk=None):
    """ユーザー作成・更新共通のフィールドバリデーション。エラー辞書を返す。"""
    errors = {}
    if not username:
        errors['username'] = 'ユーザー名を入力してください'
    else:
        qs = User.objects.filter(username=username)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        if qs.exists():
            errors['username'] = 'このユーザー名は既に使用されています'
    if not user_gender:
        errors['user_gender'] = '性別を選択してください'
    if not authority:
        errors['authority'] = '権限を選択してください'
    if int(authority or 0) == AUTHORITY_SHOP and not shop_id:
        errors['shop'] = '店舗スタッフには所属店舗が必要です'
    if int(authority or 0) == AUTHORITY_WAREHOUSE and not warehouse_id:
        errors['warehouse'] = '倉庫スタッフには所属倉庫が必要です'
    return errors


def validate_password(password1, password2, required=True):
    """パスワードバリデーション。エラー辞書を返す。"""
    errors = {}
    if not password1:
        if required:
            errors['password1'] = 'パスワードを入力してください'
    elif len(password1) < 8:
        errors['password1'] = 'パスワードは8文字以上で入力してください'
    elif password1 != password2:
        errors['password2'] = 'パスワードが一致しません'
    return errors
