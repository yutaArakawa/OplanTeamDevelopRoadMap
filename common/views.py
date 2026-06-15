from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.seializers import ShopNameSerializer, WarehouseNameSerializer

from inventory.models import (
    Shop, Warehouse
)
# Create your views here.


class ShopNameAutoCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '')
        shops = Shop.active_objects.filter(shop_name__icontains=query)[:10]
        serializer = ShopNameSerializer(shops, many=True)
        return Response(serializer.data)

class WarehouseNameAutoCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '')
        warehouses = Warehouse.active_objects.filter(warehouse_name__icontains=query)[:10]
        serializer = WarehouseNameSerializer(warehouses, many=True)
        return Response(serializer.data)
