from django import forms
from inquiry.models import Inquiry
from accounts.models import Authority
from inventory.models import Relation
from common.constants import AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE


class InquiryCreateForm(forms.ModelForm):
    """ログイン済みユーザー（管理者以外）用 問い合わせ送信フォーム"""

    class Meta:
        model = Inquiry
        fields = ['to_authority', 'to_relation', 'inquiry_title', 'inquiry_details']

    def __init__(self, *args, login_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_user = login_user

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['to_authority'].widget.attrs.update({'class': 'form-select'})
        self.fields['to_relation'].widget.attrs.update({'class': 'form-select'})
        self.fields['to_relation'].required = False
        self.fields['inquiry_details'].widget = forms.Textarea(
            attrs={'class': 'form-control', 'rows': 6}
        )

        if login_user:
            # モデルの clean() が from_user を参照するため事前にセット
            self.instance.from_user = login_user

            # 宛先権限: 自分と異なる権限のみ選択可能
            self.fields['to_authority'].queryset = Authority.objects.exclude(
                id=login_user.authority_id
            )

            # to_relation: ログインユーザーの所属に連携している Relation のみ
            if login_user.authority_id == AUTHORITY_SHOP:
                self.fields['to_relation'].queryset = Relation.active_objects.filter(
                    shop=login_user.shop
                )
            elif login_user.authority_id == AUTHORITY_WAREHOUSE:
                self.fields['to_relation'].queryset = Relation.active_objects.filter(
                    warehouse=login_user.warehouse
                )
            else:
                self.fields['to_relation'].queryset = Relation.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        to_authority = cleaned_data.get('to_authority')
        to_relation = cleaned_data.get('to_relation')

        # 宛先が店舗・倉庫スタッフの場合は to_relation 必須
        if to_authority and to_authority.id in (AUTHORITY_SHOP, AUTHORITY_WAREHOUSE):
            if not to_relation:
                self.add_error(
                    'to_relation',
                    '宛先が店舗スタッフまたは倉庫スタッフの場合は所属を選択してください。'
                )

        return cleaned_data

    def save(self, commit=True):
        inquiry = super().save(commit=False)
        user = self.login_user
        inquiry.from_user = user
        inquiry.from_authority = user.authority
        if user.authority_id == AUTHORITY_SHOP:
            inquiry.from_belong_shop = user.shop
        elif user.authority_id == AUTHORITY_WAREHOUSE:
            inquiry.from_belong_warehouse = user.warehouse

        # 宛先が管理者の場合は to_relation 不要
        if inquiry.to_authority_id == AUTHORITY_ADMIN:
            inquiry.to_relation = None

        if commit:
            inquiry.save()
        return inquiry


class InquiryGuestCreateForm(forms.ModelForm):
    """未ログインユーザー用 問い合わせ送信フォーム（宛先は自動的に管理者）"""

    class Meta:
        model = Inquiry
        fields = [
            'from_name', 'from_authority', 'from_belong_shop',
            'from_belong_warehouse', 'inquiry_title', 'inquiry_details',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['from_authority'].widget.attrs.update({'class': 'form-select'})
        self.fields['from_belong_shop'].widget.attrs.update({'class': 'form-select'})
        self.fields['from_belong_warehouse'].widget.attrs.update({'class': 'form-select'})
        self.fields['inquiry_details'].widget = forms.Textarea(
            attrs={'class': 'form-control', 'rows': 6}
        )

        # モデルの clean() が to_authority を参照するため事前にセット
        self.instance.to_authority_id = AUTHORITY_ADMIN

    def save(self, commit=True):
        inquiry = super().save(commit=False)
        inquiry.to_authority = Authority.objects.get(id=AUTHORITY_ADMIN)
        inquiry.from_user = None
        if commit:
            inquiry.save()
        return inquiry


class InquiryStatusUpdateForm(forms.ModelForm):
    """ステータス更新フォーム（受信者のみ使用）"""

    class Meta:
        model = Inquiry
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget.attrs.update({'class': 'form-select'})
