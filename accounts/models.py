from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
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

class Authority(BaseModel):
    authority_name = models.CharField(max_length=50)
    delete_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.authority_name

class CustomUserManager(UserManager):

    def create_superuser(
        self,
        username,
        email=None,
        password=None,
        **extra_fields
    ):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # 必須項目を追加
        if "user_gender" not in extra_fields:
            extra_fields["user_gender"] = User.Gender.OTHERS

        # authority を必須設定
        if "authority" not in extra_fields:
            extra_fields["authority"] = Authority.objects.get(id=1)

        return super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields
        )

class User(AbstractUser):

    objects = CustomUserManager()
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
        'inventory.Warehouse',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    shop = models.ForeignKey(
        'inventory.Shop',
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