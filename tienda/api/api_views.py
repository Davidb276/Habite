from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext as _

from tienda.models import Producto, Cliente, Pedido
from tienda.api.serializers import (
    ProductoSerializer, 
    PedidoSerializer,
    CrearPedidoRequestSerializer,
    ClienteSerializer,
    CarritoSerializer,
    AgregarAlCarritoSerializer,
    CheckoutCarritoSerializer,
    PagoSerializer,
    EnvioSerializer,
    CompraCompleteSerializer
)
from tienda.services import PedidoService, EnvioService, PagoService, CartService
from tienda.infra.factories import PasarelaFactory


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
                {"error": _("Producto no encontrado")},
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
                {"error": _("Validación fallida"), "detalles": serializer.errors},
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

            # Crear pedido usando servicio y asociar usuario si está autenticado
            service = PedidoService()
            usuario = request.user if request.user.is_authenticated else None
            pedido = service.crear_pedido(cliente_id, productos_data, usuario=usuario)

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
                {"error": _("Pedido no encontrado")},
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


class MiClienteAPI(APIView):
    """API para obtener o crear automáticamente el cliente del usuario autenticado."""

    def get(self, request):
        """Obtiene o crea automáticamente el cliente para el usuario autenticado."""
        if not request.user.is_authenticated:
            return Response(
                {"error": _("Usuario no autenticado")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Intentar obtener cliente existente por email del usuario
            cliente, created = Cliente.objects.get_or_create(
                email=request.user.email,
                defaults={
                    'nombre': request.user.get_full_name() or request.user.username,
                    'direccion': _("Por definir"),
                    'telefono': _("Por definir")
                }
            )
            
            serializer = ClienteSerializer(cliente)
            return Response(
                {
                    "cliente": serializer.data,
                    "creado": created
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarritoAPI(APIView):
    """API para obtener el carrito de un cliente."""

    def get(self, request, cliente_id):
        """Obtiene el carrito del cliente."""
        try:
            carrito = CartService.obtener_carrito(cliente_id)
            serializer = CarritoSerializer(carrito)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgregarAlCarritoAPI(APIView):
    """API para agregar items al carrito."""

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Agrega un producto al carrito.
        Requiere que el usuario esté autenticado.
        
        Entrada esperada:
        {
            "cliente_id": 1,
            "producto_id": 1,
            "cantidad": 2
        }
        """
        # Verificar si el usuario está autenticado
        if not request.user.is_authenticated:
            return Response(
                {
                    "error": _("Debe iniciar sesión para agregar productos al carrito"),
                    "require_login": True
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = AgregarAlCarritoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": _("Validación fallida"), "detalles": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cliente_id = serializer.validated_data["cliente_id"]
            producto_id = serializer.validated_data["producto_id"]
            cantidad = serializer.validated_data["cantidad"]
            
            CartService.agregar_item(cliente_id, producto_id, cantidad)
            
            carrito = CartService.obtener_carrito(cliente_id)
            carrito_serializer = CarritoSerializer(carrito)
            
            return Response(
                {
                    "mensaje": _("Producto agregado al carrito"),
                    "carrito": carrito_serializer.data
                },
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EliminarDelCarritoAPI(APIView):
    """API para eliminar items del carrito."""

    @method_decorator(csrf_exempt)
    def delete(self, request, cliente_id, producto_id):
        """Elimina un producto del carrito."""
        try:
            CartService.eliminar_item(cliente_id, producto_id)
            
            carrito = CartService.obtener_carrito(cliente_id)
            carrito_serializer = CarritoSerializer(carrito)
            
            return Response(
                {
                    "mensaje": _("Producto eliminado del carrito"),
                    "carrito": carrito_serializer.data
                },
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VaciarCarritoAPI(APIView):
    """API para vaciar el carrito."""

    @method_decorator(csrf_exempt)
    def post(self, request, cliente_id):
        """Vacía el carrito del cliente."""
        try:
            CartService.vaciar_carrito(cliente_id)
            
            return Response(
                {"mensaje": _("Carrito vaciado exitosamente")},
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckoutCarritoAPI(APIView):
    """API para procesar la compra desde el carrito."""

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Procesa la compra completa: pedido, pago y envío.
        
        Entrada esperada:
        {
            "cliente_id": 1,
            "metodo_pago": "Tarjeta de Crédito",
            "direccion_entrega": "Calle Principal 123"
        }
        """
        # Verificar que el usuario está autenticado
        if not request.user.is_authenticated:
            return Response(
                {"error": _("Debe iniciar sesión para completar la compra")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = CheckoutCarritoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": _("Validación fallida"), "detalles": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cliente_id = serializer.validated_data["cliente_id"]
            metodo_pago = serializer.validated_data["metodo_pago"]
            direccion_entrega = serializer.validated_data["direccion_entrega"]

            # Inyectar dependencias para cumplir DIP (Dependency Inversion Principle)
            cart_service = CartService(
                pedido_service=PedidoService(),
                pago_service=PagoService(pasarela=PasarelaFactory.crear_pasarela()),
                envio_service=EnvioService()
            )
            resultado = cart_service.crear_pedido_desde_carrito(
                cliente_id,
                metodo_pago,
                direccion_entrega,
                usuario=request.user
            )

            from tienda.tasks import enviar_notificacion_compra_async, generar_reporte_ventas_async
            enviar_notificacion_compra_async.delay(
                resultado["pedido"].id,
                request.user.email,
                float(resultado["pedido"].total),
                metodo_pago,
            )
            generar_reporte_ventas_async.delay()
            
            # Obtener información del usuario autenticado
            usuario_info = {
                "nombre": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
                "username": request.user.username
            }
            
            # Retornar detalles completos de la compra
            compra_data = {
                "pedido": PedidoSerializer(resultado["pedido"]).data,
                "pago": PagoSerializer(resultado["pago"]).data,
                "envio": EnvioSerializer(resultado["envio"]).data
            }
            
            return Response(
                {
                    "mensaje": _("Compra procesada exitosamente"),
                    "usuario": usuario_info,
                    "compra": compra_data
                },
                status=status.HTTP_201_CREATED
            )
        except Cliente.DoesNotExist:
            return Response(
                {"error": _("Cliente no encontrado")},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
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


class PagoDetalleAPI(APIView):
    """API para obtener detalles de un pago."""

    def get(self, request, pago_id):
        """Obtiene los detalles de un pago."""
        try:
            from tienda.models import Pago
            pago = Pago.objects.get(id=pago_id)
            serializer = PagoSerializer(pago)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Pago no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )


class EnvioDetalleAPI(APIView):
    """API para obtener detalles de un envío."""

    def get(self, request, envio_id):
        """Obtiene los detalles de un envío."""
        try:
            from tienda.models import Envio
            envio = Envio.objects.get(id=envio_id)
            serializer = EnvioSerializer(envio)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Envío no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )


class ActualizarEstadoEnvioAPI(APIView):
    """API para actualizar el estado de un envío."""

    @method_decorator(csrf_exempt)
    def patch(self, request, envio_id):
        """
        Actualiza el estado de un envío.
        
        Entrada esperada:
        {
            "nuevo_estado": "En tránsito"
        }
        """
        try:
            from tienda.models import Envio
            envio = Envio.objects.get(id=envio_id)
            nuevo_estado = request.data.get("nuevo_estado")
            
            if not nuevo_estado:
                return Response(
                    {"error": "nuevo_estado es requerido"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            envio_service = EnvioService()
            envio_actualizado = envio_service.actualizar_estado_envio(envio_id, nuevo_estado)
            
            serializer = EnvioSerializer(envio_actualizado)
            return Response(
                {
                    "mensaje": "Estado de envío actualizado",
                    "envio": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MisPedidosAPI(APIView):
    """API para obtener los pedidos del usuario actual."""

    def get(self, request):
        """Obtiene todos los pedidos del usuario autenticado."""
        try:
            if not request.user.is_authenticated:
                return Response(
                    {"error": _("Usuario no autenticado")},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            pedidos = (
                Pedido.objects.filter(
                    Q(usuario=request.user) |
                    Q(usuario__isnull=True, cliente__email=request.user.email)
                )
                .order_by('-fecha')
            )
            serializer = PedidoSerializer(pedidos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TodosPedidosAPI(APIView):
    """API para que admins obtengan todos los pedidos."""

    def get(self, request):
        """Obtiene todos los pedidos (solo para admins)."""
        try:
            if not request.user.is_superuser:
                return Response(
                    {"error": _("Acceso denegado")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            pedidos = Pedido.objects.all().order_by('-fecha')
            serializer = PedidoSerializer(pedidos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActualizarEstadoPedidoAPI(APIView):
    """API para actualizar el estado de un pedido."""

    @method_decorator(csrf_exempt)
    def patch(self, request, pedido_id):
        """
        Actualiza el estado de un pedido (solo para admins).
        
        Entrada esperada:
        {
            "estado": "Completado"
        }
        """
        try:
            if not request.user.is_superuser:
                return Response(
                    {"error": _("Acceso denegado")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            pedido = Pedido.objects.get(id=pedido_id)
            nuevo_estado = request.data.get("estado")
            
            if not nuevo_estado:
                return Response(
                    {"error": _("estado es requerido")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pedido.estado = nuevo_estado
            pedido.save()
            
            serializer = PedidoSerializer(pedido)
            return Response(
                {
                    "mensaje": _("Estado de pedido actualizado"),
                    "pedido": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Pedido.DoesNotExist:
            return Response(
                {"error": _("Pedido no encontrado")},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )