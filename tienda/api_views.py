from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from tienda.models import Producto, Cliente
from tienda.serializers import (
    ProductoSerializer, 
    PedidoSerializer,
    CrearPedidoRequestSerializer,
    ClienteSerializer
)
from tienda.services import PedidoService, EnvioService, PagoService


class ProductosAPI(APIView):
    """API para listar productos."""

    def get(self, request):
        """Lista todos los productos disponibles."""
        try:
            productos = Producto.objects.all()
            serializer = ProductoSerializer(productos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductoDetalleAPI(APIView):
    """API para obtener detalle de un producto específico."""

    def get(self, request, producto_id):
        """Obtiene los detalles de un producto por ID."""
        try:
            producto = Producto.objects.get(id=producto_id)
            serializer = ProductoSerializer(producto)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Producto.DoesNotExist:
            return Response(
                {"error": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CrearPedidoAPI(APIView):
    """API para crear nuevos pedidos."""

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Crea un nuevo pedido.
        
        Entrada esperada:
        {
            "cliente_id": 1,
            "productos": [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 2, "cantidad": 1}
            ]
        }
        """

        # Validar entrada
        serializer = CrearPedidoRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validación fallida", "detalles": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cliente_id = serializer.validated_data["cliente_id"]
            productos = serializer.validated_data["productos"]
            
            # Convertir formato de entrada
            productos_data = [
                (item["producto_id"], item["cantidad"]) 
                for item in productos
            ]

            # Crear pedido usando servicio
            service = PedidoService()
            pedido = service.crear_pedido(cliente_id, productos_data)

            # Retornar pedido creado
            pedido_serializer = PedidoSerializer(pedido)
            return Response(
                pedido_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            # Errores de validación de negocio
            error_message = str(e.message) if hasattr(e, 'message') else str(e)
            
            # Determinar si es conflicto (409) o solicitud incorrecta (400)
            if "Stock insuficiente" in error_message:
                return Response(
                    {"error": error_message},
                    status=status.HTTP_409_CONFLICT
                )
            else:
                return Response(
                    {"error": error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            import traceback
            return Response(
                {
                    "error": str(e),
                    "tipo": type(e).__name__,
                    "traceback": traceback.format_exc() if settings.DEBUG else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PedidoDetalleAPI(APIView):
    """API para obtener detalles de un pedido específico."""

    def get(self, request, pedido_id):
        """Obtiene los detalles completos de un pedido."""
        try:
            from tienda.models import Pedido
            pedido = Pedido.objects.get(id=pedido_id)
            serializer = PedidoSerializer(pedido)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Pedido no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )


class ClientesAPI(APIView):
    """API para gestionar clientes."""

    def get(self, request):
        """Lista todos los clientes."""
        try:
            clientes = Cliente.objects.all()
            serializer = ClienteSerializer(clientes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Crea un nuevo cliente."""
        serializer = ClienteSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )