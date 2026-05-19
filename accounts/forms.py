from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User, Authority
from common.constants import (
    AUTHORITY_ADMIN,
    AUTHORITY_SHOP,
    AUTHORITY_WAREHOUSE
)

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
            'class': 'form-select'
        })
        self.fields['user_gender'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['shop'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['warehouse'].widget.attrs.update({
            'class': 'form-select'
        })

        if user:
            # 管理者
            if user.authority_id == AUTHORITY_ADMIN:
                self.fields['authority'].queryset = Authority.objects.all()
            # 店舗スタッフ
            if user.authority_id == AUTHORITY_SHOP:
                self.fields['authority'].queryset = Authority.objects.filter(
                    id=AUTHORITY_SHOP
                )
                self.fields['authority'].initial = AUTHORITY_SHOP

            # 倉庫スタッフ
            if user.authority_id == AUTHORITY_WAREHOUSE:
                self.fields['authority'].queryset = Authority.objects.filter(
                    id=AUTHORITY_WAREHOUSE
                )
                self.fields['authority'].initial = AUTHORITY_WAREHOUSE
