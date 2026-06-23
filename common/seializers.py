from rest_framework import serializers
from inventory.models import Shop, Warehouse


class ShopNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='shop_name')

    class Meta:
        model = Shop
        fields = ['id', 'name']


class WarehouseNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='warehouse_name')

    class Meta:
        model = Warehouse
        fields = ['id', 'name']
