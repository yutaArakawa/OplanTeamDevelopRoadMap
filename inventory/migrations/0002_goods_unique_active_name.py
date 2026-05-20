from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='goods',
            constraint=models.UniqueConstraint(
                fields=('goods_name',),
                condition=models.Q(delete_flg=False),
                name='unique_active_goods_name',
            ),
        ),
    ]
