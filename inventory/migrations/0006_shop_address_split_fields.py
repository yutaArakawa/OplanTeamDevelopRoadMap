from django.db import migrations, models

from inventory.constants.prefectures import PREFECTURE_CHOICES


def populate_shop_split_address(apps, schema_editor):
    Shop = apps.get_model('inventory', 'Shop')

    for shop in Shop.objects.all():
        shop.address1 = shop.address
        shop.save(update_fields=['address1'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_shop_address_single_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='prefecture',
            field=models.CharField(blank=True, choices=PREFECTURE_CHOICES, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='shop',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='shop',
            name='address1',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='shop',
            name='address2',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RunPython(populate_shop_split_address, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='shop',
            name='address',
        ),
    ]
