from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from tienda.models import Producto
from tienda.serializers import ProductoSerializer
from tienda.services import PedidoService


class ProductosAPI(APIView):

    def get(self, request):
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)

        return Response(serializer.data)


class CrearPedidoAPI(APIView):

    def post(self, request):

        cliente_id = request.data.get("cliente_id")
        productos = request.data.get("productos")

        if not cliente_id or not productos:
            return Response(
                {"error": "Datos incompletos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = PedidoService()
        pedido = service.crear_pedido(cliente_id, productos)

        return Response(
            {"pedido_id": pedido.id},
            status=status.HTTP_201_CREATED
        )