from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_goods_unique_active_name'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='goodscategory',
            constraint=models.UniqueConstraint(
                fields=('category_name',),
                condition=models.Q(delete_flg=False),
                name='unique_active_category_name',
            ),
        ),
    ]
