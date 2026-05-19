from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

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


class Inquiry(BaseModel):

    class Status(models.IntegerChoices):
        PENDING = 0, '未対応'
        IN_PROGRESS = 1, '対応中'
        COMPLETED = 2, '対応済み'

    to_authority = models.ForeignKey(
        'accounts.Authority',
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
        'accounts.Authority',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    from_belong_shop = models.ForeignKey(
        'inventory.Shop',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    from_belong_warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    to_relation = models.ForeignKey(
        'inventory.Relation',
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