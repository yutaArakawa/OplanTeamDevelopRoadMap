from django.db import models

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

class MonthlyOrderSummary(BaseModel):
    count_date = models.DateField()
    shop = models.ForeignKey(
        'inventory.Shop',
        on_delete=models.PROTECT
    )
    goods = models.ForeignKey(
        'inventory.Goods',
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