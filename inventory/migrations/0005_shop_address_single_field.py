from django.db import migrations, models


def populate_shop_address(apps, schema_editor):
    Shop = apps.get_model('inventory', 'Shop')

    for shop in Shop.objects.all():
        parts = [
            getattr(shop, 'prefecture', '') or '',
            getattr(shop, 'city', '') or '',
            getattr(shop, 'address1', '') or '',
            getattr(shop, 'address2', '') or '',
        ]
        shop.address = ''.join(parts)
        shop.save(update_fields=['address'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_warehouse_unique_active_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='address',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
        migrations.RunPython(populate_shop_address, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='shop',
            name='address1',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='address2',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='city',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='prefecture',
        ),
        migrations.AlterField(
            model_name='shop',
            name='address',
            field=models.CharField(max_length=255),
        ),
    ]
