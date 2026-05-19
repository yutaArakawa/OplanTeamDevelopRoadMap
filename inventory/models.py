from django.db import models
from django.core.exceptions import ValidationError
from .constants.prefectures import PREFECTURE_CHOICES

# Create your models here.
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(delete_flg=False)

class BaseModel(models.Model):
    delete_flg = models.BooleanField(default=False)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        abstract = True

class Warehouse(BaseModel):
    warehouse_name = models.CharField(max_length=255)
    prefecture = models.CharField(
        max_length=10,
        choices=PREFECTURE_CHOICES
    )
    city = models.CharField(max_length=100)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.warehouse_name

class Shop(BaseModel):
    shop_name = models.CharField(max_length=255)
    prefecture = models.CharField(
        max_length=10,
        choices=PREFECTURE_CHOICES
    )
    city = models.CharField(max_length=100)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name

class GoodsCategory(BaseModel):
    category_name = models.CharField(max_length=255)
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category_name

class Goods(BaseModel):
    goods_name = models.CharField(max_length=255)
    goods_category = models.ForeignKey(
        'GoodsCategory',
        on_delete=models.PROTECT
    )
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['goods_name'],
                condition=models.Q(delete_flg=False),
                name='unique_active_goods_name'
            )
        ]

    def clean(self):
        super().clean()

        duplicate_goods = Goods.active_objects.filter(goods_name=self.goods_name)
        if self.pk:
            duplicate_goods = duplicate_goods.exclude(pk=self.pk)

        if duplicate_goods.exists():
            raise ValidationError({
                'goods_name': '同じ商品名は登録できません。'
            })

    def has_related_records(self):
        return (
            self.shopstock_set.filter(delete_flg=False).exists()
            or self.warehousestock_set.filter(delete_flg=False).exists()
            or self.ordergoods_set.filter(delete_flg=False).exists()
        )

    def soft_delete(self):
        self.delete_flg = True
        self.save(update_fields=['delete_flg', 'updated_at'])

    def __str__(self):
        return self.goods_name

class ShopStock(BaseModel):
    shop = models.ForeignKey(
        'Shop',
        on_delete=models.PROTECT
    )
    goods = models.ForeignKey(
        'Goods',
        on_delete=models.PROTECT
    )
    stock = models.PositiveIntegerField(default=0)
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.shop} - {self.goods} : {self.stock}'

class WarehouseStock(BaseModel):
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.PROTECT
    )
    goods = models.ForeignKey(
        'Goods',
        on_delete=models.PROTECT
    )
    stock = models.PositiveIntegerField(default=0)
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.warehouse} - {self.goods} : {self.stock}'

class Relation(BaseModel):
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.PROTECT
    )
    shop = models.ForeignKey(
        'Shop',
        on_delete=models.PROTECT
    )
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['warehouse', 'shop'],
                name='unique_warehouse_shop'
            )
        ]

    def __str__(self):
        return f'{self.warehouse} - {self.shop}'

class Order(BaseModel):

    class Status(models.IntegerChoices):
        ORDERED   = 0, '発注済'
        PREPARING = 1, '準備中'
        SHIPPED   = 2, '発送済み'
        DELIVERED = 3, '納品済み'
        CANCELED  = 4, 'キャンセル'
        
    relation = models.ForeignKey(
        'Relation',
        on_delete=models.PROTECT
    )
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.ORDERED
    )
    ordered_at = models.DateTimeField(auto_now_add=True)
    shipped_at = models.DateTimeField(
        null=True,
        blank=True
    )
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'受注ID：{self.id}'
    
class OrderGoods(BaseModel):
    order = models.ForeignKey(
        'Order',
        on_delete=models.PROTECT
    )
    goods = models.ForeignKey(
        'Goods',
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField()
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'goods'],
                name='unique_order_goods'
            )
        ]

    def __str__(self):
        return f'{self.order} - {self.goods} : {self.quantity}'
