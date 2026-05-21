from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_goodscategory_unique_active_category_name'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='warehouse',
            constraint=models.UniqueConstraint(
                fields=('warehouse_name',),
                condition=models.Q(('delete_flg', False)),
                name='unique_active_warehouse_name',
            ),
        ),
    ]
