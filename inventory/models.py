from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
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

class Authority(BaseModel):
    authority_name = models.CharField(max_length=50)
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.authority_name

class User(AbstractUser):

    objects = UserManager()
    active_objects = ActiveManager()

    class Gender(models.IntegerChoices):
        MEN = 1, '男'
        WOMEN = 2, '女'
        OTHERS = 3, 'その他'

    username = models.CharField(
        max_length=255,
        unique=True
    )
    user_gender = models.IntegerField(
        choices=Gender.choices,
    )
    authority = models.ForeignKey(
        'Authority',
        on_delete=models.PROTECT
    )
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    shop = models.ForeignKey(
        'Shop',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        authority_id = self.authority.id
        if authority_id == 2:
            if not self.shop:
                raise ValidationError({
                    'shop': '店舗を選択してください。'
                })
        elif authority_id == 3:
            if not self.warehouse:
                raise ValidationError({
                    'warehouse': '倉庫を選択してください。'
                })

    def __str__(self):
        return self.username

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

class Inquiry(BaseModel):

    class Status(models.IntegerChoices):
        PENDING = 0, '未対応'
        IN_PROGRESS = 1, '対応中'
        COMPLETED = 2, '対応済み'

    to_authority = models.ForeignKey(
        'Authority',
        on_delete=models.PROTECT,
        related_name='received_inquiries'
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    from_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    from_authority = models.ForeignKey(
        'Authority',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    from_belong_shop = models.ForeignKey(
        'Shop',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    from_belong_warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    to_relation = models.ForeignKey(
        'Relation',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    inquiry_title =models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    inquiry_details =models.CharField(
        max_length=255
    )
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.PENDING
    )
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # ログインユーザーの場合
        if self.from_user:
            if self.from_user.authority_id == self.to_authority_id:
                raise ValidationError({
                    'to_authority': '自分と異なる権限の宛先を選択してください。'
                })
        else:
            if self.to_authority.id != 1:
                raise ValidationError({
                    'to_authority': '未ログインユーザーは管理者宛のみ送信可能です。'
                })

    def __str__(self):
        return f'問い合わせID:{self.id}'

class MonthlyOrderSummary(BaseModel):
    count_date = models.DateField()
    shop = models.ForeignKey(
        'Shop',
        on_delete=models.PROTECT
    )
    goods = models.ForeignKey(
        'Goods',
        on_delete=models.PROTECT
    )
    total_quantity = models.PositiveIntegerField(
        default=0
    )
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['count_date', 'shop', 'goods'],
                name='unique_summary'
            )
        ]

    def __str__(self):
        return (
            f'集計日:{self.count_date}'
            f'店舗:{self.shop.shop_name}'
            f'商品:{self.goods.goods_name}'
            f'発注数:{self.total_quantity}'
        )
