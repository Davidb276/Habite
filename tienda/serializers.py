from rest_framework import serializers
from tienda.models import Producto, Pedido, PedidoItem


class ProductoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Producto
        fields = "__all__"


class PedidoItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = PedidoItem
        fields = ["producto", "cantidad"]


class PedidoSerializer(serializers.ModelSerializer):

    items = PedidoItemSerializer(many=True)

    class Meta:
        model = Pedido
        fields = ["id", "cliente", "total", "items"]    