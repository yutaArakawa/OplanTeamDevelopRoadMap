from django import forms
from inventory.models import Goods, GoodsCategory, Relation, Shop, ShopStock, Warehouse, WarehouseStock

class GoodsCategoryForm(forms.ModelForm):
    class Meta:
        model = GoodsCategory
        fields = ('category_name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category_name'].widget.attrs.update({
            'class': 'form-control'
        })

class GoodsCreateForm(forms.ModelForm):
    class Meta:
        model = Goods
        fields = ('goods_name', 'goods_category')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['goods_name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['goods_category'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['goods_category'].queryset = GoodsCategory.active_objects.order_by('category_name')


class WarehouseCreateForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ('warehouse_name', 'prefecture', 'city', 'address1', 'address2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['warehouse_name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['prefecture'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['city'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['address1'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['address2'].widget.attrs.update({
            'class': 'form-control'
        })


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ('shop_name', 'prefecture', 'city', 'address1', 'address2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['shop_name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['prefecture'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['city'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['address1'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['address2'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['prefecture'].required = True
        self.fields['city'].required = True
        self.fields['address1'].required = True

    def clean_shop_name(self):
        shop_name = self.cleaned_data.get('shop_name')
        qs = Shop.active_objects.filter(shop_name=shop_name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('既に店舗名は存在します')
        return shop_name


class RelationForm(forms.ModelForm):
    class Meta:
        model = Relation
        fields = ('shop', 'warehouse')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['shop'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['warehouse'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['shop'].queryset = Shop.active_objects.order_by('shop_name')
        self.fields['warehouse'].queryset = Warehouse.active_objects.order_by('warehouse_name')

    def clean(self):
        cleaned_data = super().clean()
        shop = cleaned_data.get('shop')
        warehouse = cleaned_data.get('warehouse')

        if not shop or not warehouse:
            return cleaned_data

        if Relation.active_objects.filter(shop=shop, warehouse=warehouse).exists():
            raise forms.ValidationError(
                '選択した店舗と倉庫の組み合わせは既に登録されています。'
            )

        return cleaned_data

class ShopStockEditForm(forms.ModelForm):
    class Meta:
        model = ShopStock
        fields = ('stock',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['stock'].widget = forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
            'min': '0',
        })

class WarehouseStockEditForm(forms.ModelForm):
    class Meta:
        model = WarehouseStock
        fields = ('stock',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['stock'].widget = forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
            'min': '0',
        })

class OrderForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
        })
    )
