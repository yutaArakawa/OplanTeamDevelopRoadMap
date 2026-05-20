from django import forms
from inventory.models import Goods, GoodsCategory, Warehouse

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
