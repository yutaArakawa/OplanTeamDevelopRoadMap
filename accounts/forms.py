from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from accounts.models import User, Authority
from inventory.models import Shop, Warehouse
from common.constants import (
    AUTHORITY_ADMIN,
    AUTHORITY_SHOP,
    AUTHORITY_WAREHOUSE
)

class LoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if user.delete_flg:
            raise ValidationError(
                'このアカウントは削除されています。',
                code='inactive',
            )
        super().confirm_login_allowed(user)

class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            'username',
            'password1',
            'password2',
            'user_gender',
            'authority',
            'shop',
            'warehouse',
        )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })

        self.fields['authority'].widget.attrs.update({
            'class': 'form-select',
            'id': 'authority-select'
        })
        self.fields['user_gender'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['shop'].widget.attrs.update({
            'class': 'form-select',
            'id': 'belonging-select-shop'
        })
        self.fields['warehouse'].widget.attrs.update({
            'class': 'form-select',
            'id': 'belonging-select-warehouse'
        })
        self.fields['shop'].queryset = Shop.active_objects.order_by('shop_name')
        self.fields['warehouse'].queryset = Warehouse.active_objects.order_by('warehouse_name')

        if user:
            # 管理者
            if user.authority_id == AUTHORITY_ADMIN:
                self.fields['authority'].queryset = Authority.active_objects.all()
            # 店舗スタッフ
            if user.authority_id == AUTHORITY_SHOP:
                self.fields['authority'].queryset = Authority.active_objects.filter(
                    id=AUTHORITY_SHOP
                )
                self.fields['authority'].initial = AUTHORITY_SHOP

            # 倉庫スタッフ
            if user.authority_id == AUTHORITY_WAREHOUSE:
                self.fields['authority'].queryset = Authority.active_objects.filter(
                    id=AUTHORITY_WAREHOUSE
                )
                self.fields['authority'].initial = AUTHORITY_WAREHOUSE

class UserUpdateForm(UserChangeForm):
    new_password1 = forms.CharField(
        label='新しいパスワード',
        widget=forms.PasswordInput,
        required=False
    )
    new_password2 = forms.CharField(
        label='新しいパスワード（確認）',
        widget=forms.PasswordInput,
        required=False
    )
    class Meta:
        model = User
        fields = (
            'username',
            'user_gender',
            'authority',
            'shop',
            'warehouse',
        )

    def __init__(self, *args, user=None, **kwargs):
        self.login_user = user
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })

        self.fields['authority'].widget.attrs.update({
            'class': 'form-select',
            'id': 'authority-select'
        })
        self.fields['user_gender'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['shop'].widget.attrs.update({
            'class': 'form-select',
            'id': 'belonging-select-shop'
        })
        self.fields['warehouse'].widget.attrs.update({
            'class': 'form-select',
            'id': 'belonging-select-warehouse'
        })
        self.fields['shop'].queryset = Shop.active_objects.order_by('shop_name')
        self.fields['warehouse'].queryset = Warehouse.active_objects.order_by('warehouse_name')

        if user:
            # 店舗スタッフ
            if user.authority_id == AUTHORITY_SHOP:
                self.fields['username'].disabled = True
                self.fields['new_password1'].disabled = True
                self.fields['new_password2'].disabled = True
                self.fields['user_gender'].disabled = True
                self.fields['authority'].disabled = True
                self.fields.pop('warehouse')

            # 倉庫スタッフ
            if user.authority_id == AUTHORITY_WAREHOUSE:
                self.fields['username'].disabled = True
                self.fields['new_password1'].disabled = True
                self.fields['new_password2'].disabled = True
                self.fields['user_gender'].disabled = True
                self.fields['authority'].disabled = True
                self.fields.pop('shop')

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p1 != p2:
            raise ValidationError('パスワードが一致しません。')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('new_password1')
        if password:
            user.set_password(password)

        # 店舗スタッフと倉庫スタッフは権限を変更できないようにする
        if self.login_user.authority_id == AUTHORITY_SHOP or self.login_user.authority_id == AUTHORITY_WAREHOUSE:
            user.authority = self.instance.authority
            user.username = self.instance.username
            user.user_gender = self.instance.user_gender

        if commit:
            user.save()
        return user