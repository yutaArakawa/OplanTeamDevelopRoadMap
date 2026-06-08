from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_alter_shop_address1_alter_shop_city_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='relation',
            name='unique_warehouse_shop',
        ),
        migrations.AddConstraint(
            model_name='relation',
            constraint=models.UniqueConstraint(
                fields=('warehouse', 'shop'),
                condition=models.Q(delete_flg=False),
                name='unique_active_warehouse_shop',
            ),
        ),
    ]
