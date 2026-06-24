from rest_framework.views import APIView
from rest_framework.response import Response
from common.seializers import ShopNameSerializer, WarehouseNameSerializer
from inventory.constants.prefectures import PREFECTURE_CHOICES

from inventory.models import (Shop, Warehouse)


class ShopNameAutoCompleteView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')
        shops = Shop.active_objects.filter(shop_name__icontains=query)[:10]
        serializer = ShopNameSerializer(shops, many=True)
        return Response(serializer.data)


class WarehouseNameAutoCompleteView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')
        warehouses = Warehouse.active_objects.filter(warehouse_name__icontains=query)[:10]
        serializer = WarehouseNameSerializer(warehouses, many=True)
        return Response(serializer.data)


class PrefectureNameAutoCompleteView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')
        prefectures = [
            {'id': code, 'name': name}
            for code, name in PREFECTURE_CHOICES
            if query in name
        ]
        return Response(prefectures)
