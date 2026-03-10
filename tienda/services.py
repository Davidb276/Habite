from django.db import transaction
from tienda.domain.builders import PedidoBuilder
from tienda.infra.factories import NotificadorFactory
from tienda.models import Cliente, Producto, Pedido, Inventario, Pago, Envio
from django.core.exceptions import ValidationError


class InventarioService:
    """Gestiona la lógica de negocio para inventario."""
    
    @staticmethod
    def verificar_disponibilidad(producto_id, cantidad):
        """Valida si hay stock disponible del producto."""
        try:
            inventario = Inventario.objects.get(producto_id=producto_id)
            return inventario.cantidad_disponible >= cantidad
        except Inventario.DoesNotExist:
            return False
    
    @staticmethod
    def reducir_stock(producto_id, cantidad):
        """Reduce el stock del producto. Lanza excepción si no hay suficiente."""
        try:
            inventario = Inventario.objects.get(producto_id=producto_id)
            if inventario.cantidad_disponible < cantidad:
                raise ValidationError(
                    f"Stock insuficiente. Disponible: {inventario.cantidad_disponible}"
                )
            inventario.cantidad_disponible -= cantidad
            inventario.save()
            return True
        except Inventario.DoesNotExist:
            raise ValidationError("Inventario no encontrado para este producto")


class PedidoService:
    """Orquesta la lógica de creación y gestión de pedidos."""
    
    def __init__(self):
        self.notificador = NotificadorFactory.crear_notificador()
    
    @transaction.atomic
    def crear_pedido(self, cliente_id, productos_data):
        """
        Crea un pedido con validación de stock y cálculo de total.
        
        Args:
            cliente_id: ID del cliente
            productos_data: Lista de tuplas (producto_id, cantidad)
        
        Returns:
            Pedido creado
        
        Raises:
            ValidationError: Si hay validaciones que fallan
        """
        # Validar cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            raise ValidationError("Cliente no encontrado")
        
        # Validar y reservar stock
        for prod_id, cantidad in productos_data:
            try:
                Producto.objects.get(id=prod_id)
            except Producto.DoesNotExist:
                raise ValidationError(f"Producto {prod_id} no encontrado")
            
            if not InventarioService.verificar_disponibilidad(prod_id, cantidad):
                raise ValidationError(f"Stock insuficiente para producto {prod_id}")
        
        # Construir pedido usando Builder
        builder = PedidoBuilder().para_cliente(cliente)
        
        for prod_id, cantidad in productos_data:
            producto = Producto.objects.get(id=prod_id)
            builder.agregar_item(producto, cantidad)
            # Reducir stock después de validar
            InventarioService.reducir_stock(prod_id, cantidad)
        
        pedido = builder.build()
        
        # Calcular y establecer total
        self._calcular_total_pedido(pedido)
        
        # Notificar
        self.notificador.enviar(pedido)
        
        return pedido
    
    @staticmethod
    def _calcular_total_pedido(pedido):
        """Calcula el total del pedido basado en sus items."""
        total = sum(item.producto.precio * item.cantidad for item in pedido.items.all())
        pedido.total = total
        pedido.save()
        return total
    
    @staticmethod
    def actualizar_estado_pedido(pedido_id, nuevo_estado):
        """Actualiza el estado del pedido."""
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            pedido.estado = nuevo_estado
            pedido.save()
            return pedido
        except Pedido.DoesNotExist:
            raise ValidationError("Pedido no encontrado")


class PagoService:
    """Gestiona la lógica de procesamiento de pagos."""
    
    @staticmethod
    def procesear_pago(pedido_id, metodo_pago, monto):
        """
        Procesa el pago de un pedido.
        
        Raises:
            ValidationError: Si el pedido no existe o hay conflicto
        """
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            raise ValidationError("Pedido no encontrado")
        
        # Validar que el monto coincida
        if monto != pedido.total:
            raise ValidationError(f"Monto incorrecto. Total esperado: {pedido.total}")
        
        # Crear registro de pago
        pago = Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo_pago,
            monto=monto,
            estado="Pagado"
        )
        
        # Actualizar estado del pedido
        pedido.estado = "Pagado"
        pedido.save()
        
        return pago
    
    @staticmethod
    def obtener_pago_pedido(pedido_id):
        """Obtiene el registro de pago de un pedido."""
        try:
            return Pago.objects.get(pedido_id=pedido_id)
        except Pago.DoesNotExist:
            return None


class EnvioService:
    """Gestiona la lógica de envíos."""
    
    @staticmethod
    def crear_envio(pedido_id, direccion_entrega):
        """Crea un registro de envío para un pedido."""
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            raise ValidationError("Pedido no encontrado")
        
        envio = Envio.objects.create(
            pedido=pedido,
            direccion_entrega=direccion_entrega,
            estado_envio="Preparando"
        )
        return envio
    
    @staticmethod
    def actualizar_estado_envio(envio_id, nuevo_estado):
        """Actualiza el estado del envío."""
        try:
            envio = Envio.objects.get(id=envio_id)
            envio.estado_envio = nuevo_estado
            envio.save()
            return envio
        except Envio.DoesNotExist:
            raise ValidationError("Envío no encontrado")
