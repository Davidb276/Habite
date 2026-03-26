from rest_framework import serializers
from tienda.models import Producto, Pedido, PedidoItem, Cliente, Carrito, CarritoItem, Pago, Envio
from tienda.services import InventarioService


class ProductoSerializer(serializers.ModelSerializer):
    """Serializer para productos con validaciones."""

    class Meta:
        model = Producto
        fields = "__all__"
    
    def validate_precio(self, value):
        """Valida que el precio sea positivo."""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")
        return value


class PedidoItemSerializer(serializers.ModelSerializer):
    """Serializer para items del pedido con validaciones."""

    producto_id = serializers.SerializerMethodField(read_only=True)
    producto_nombre = serializers.SerializerMethodField(read_only=True)
    precio_unitario = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PedidoItem
        fields = ["id", "producto_id", "producto_nombre", "precio_unitario", "cantidad"]
    
    def get_producto_id(self, obj):
        """Retorna el ID del producto."""
        return obj.producto.id if obj.producto else None
    
    def get_producto_nombre(self, obj):
        """Retorna el nombre del producto."""
        return obj.producto.nombre if obj.producto else None
    
    def get_precio_unitario(self, obj):
        """Retorna el precio unitario del producto."""
        return float(obj.producto.precio) if obj.producto else 0
    
    def validate_cantidad(self, value):
        """Valida que la cantidad sea positiva."""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value


class PedidoSerializer(serializers.ModelSerializer):
    """Serializer para pedidos con validaciones anidadas."""

    items = PedidoItemSerializer(many=True, read_only=True)
    cliente_id = serializers.SerializerMethodField(read_only=True)
    usuario_id = serializers.SerializerMethodField(read_only=True)
    usuario_username = serializers.SerializerMethodField(read_only=True)
    usuario_email = serializers.SerializerMethodField(read_only=True)
    total = serializers.SerializerMethodField(read_only=True)
    fecha = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "cliente_id",
            "usuario_id",
            "usuario_username",
            "usuario_email",
            "total",
            "estado",
            "fecha",
            "items",
        ]
        read_only_fields = ["id", "total", "fecha"]
    
    def get_cliente_id(self, obj):
        """Retorna el ID del cliente."""
        return obj.cliente.id if obj.cliente else None

    def get_usuario_id(self, obj):
        """Retorna el ID del usuario asociado."""
        return obj.usuario.id if obj.usuario else None
    
    def get_usuario_username(self, obj):
        """Retorna el username del usuario."""
        return obj.usuario.username if obj.usuario else None
    
    def get_usuario_email(self, obj):
        """Retorna el email del usuario."""
        return obj.usuario.email if obj.usuario else None
    
    def get_total(self, obj):
        """Retorna el total como float."""
        return float(obj.total) if obj.total else 0.0
    
    def get_fecha(self, obj):
        """Retorna la fecha formateada."""
        return obj.fecha.strftime("%Y-%m-%d %H:%M:%S") if obj.fecha else None


class CrearPedidoRequestSerializer(serializers.Serializer):
    """Serializer para la solicitud de creación de pedido."""
    
    cliente_id = serializers.IntegerField()
    productos = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            allow_empty=False
        )
    )
    
    def validate_cliente_id(self, value):
        """Valida que el cliente exista."""
        try:
            Cliente.objects.get(id=value)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("Cliente no encontrado")
        return value
    
    def validate_productos(self, value):
        """Valida que los productos existan y tengan cantidad válida."""
        if len(value) == 0:
            raise serializers.ValidationError("Debe incluir al menos un producto")
        
        for item in value:
            if "producto_id" not in item or "cantidad" not in item:
                raise serializers.ValidationError(
                    "Cada producto debe tener 'producto_id' y 'cantidad'"
                )
            
            try:
                Producto.objects.get(id=item["producto_id"])
            except Producto.DoesNotExist:
                raise serializers.ValidationError(
                    f"Producto {item['producto_id']} no encontrado"
                )
            
            if item["cantidad"] <= 0:
                raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        
        return value


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer para clientes."""

    class Meta:
        model = Cliente
        fields = "__all__"
    
    def validate_email(self, value):
        """Valida formato de email."""
        if "@" not in value:
            raise serializers.ValidationError("Email inválido")
        return value


class CarritoItemSerializer(serializers.ModelSerializer):
    """Serializer para items del carrito."""

    producto_id = serializers.SerializerMethodField(read_only=True)
    producto_nombre = serializers.SerializerMethodField(read_only=True)
    precio_unitario = serializers.SerializerMethodField(read_only=True)
    subtotal = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CarritoItem
        fields = ["id", "producto_id", "producto_nombre", "precio_unitario", "cantidad", "subtotal"]
    
    def get_producto_id(self, obj):
        """Retorna el ID del producto."""
        return obj.producto.id
    
    def get_producto_nombre(self, obj):
        """Retorna el nombre del producto."""
        return obj.producto.nombre
    
    def get_precio_unitario(self, obj):
        """Retorna el precio unitario."""
        return float(obj.producto.precio)
    
    def get_subtotal(self, obj):
        """Retorna el subtotal del item."""
        return float(obj.producto.precio * obj.cantidad)
    
    def validate_cantidad(self, value):
        """Valida que la cantidad sea positiva."""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value


class CarritoSerializer(serializers.ModelSerializer):
    """Serializer para el carrito completo."""

    items = CarritoItemSerializer(many=True, read_only=True)
    cliente_id = serializers.SerializerMethodField(read_only=True)
    total = serializers.SerializerMethodField(read_only=True)
    cantidad_items = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Carrito
        fields = ["id", "cliente_id", "items", "total", "cantidad_items", "fecha_creacion"]
        read_only_fields = ["id", "fecha_creacion"]
    
    def get_cliente_id(self, obj):
        """Retorna el ID del cliente."""
        return obj.cliente.id
    
    def get_total(self, obj):
        """Calcula el total del carrito."""
        total = sum(
            item.producto.precio * item.cantidad 
            for item in obj.items.all()
        )
        return float(total)
    
    def get_cantidad_items(self, obj):
        """Retorna la cantidad de items en el carrito."""
        return obj.items.count()


class AgregarAlCarritoSerializer(serializers.Serializer):
    """Serializer para agregar items al carrito."""
    
    cliente_id = serializers.IntegerField()
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)
    
    def validate_cliente_id(self, value):
        """Valida que el cliente exista."""
        try:
            Cliente.objects.get(id=value)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("Cliente no encontrado")
        return value
    
    def validate_producto_id(self, value):
        """Valida que el producto exista."""
        try:
            Producto.objects.get(id=value)
        except Producto.DoesNotExist:
            raise serializers.ValidationError("Producto no encontrado")
        return value


class CheckoutCarritoSerializer(serializers.Serializer):
    """Serializer para procesar la compra desde el carrito."""
    
    cliente_id = serializers.IntegerField()
    metodo_pago = serializers.CharField(max_length=50)
    direccion_entrega = serializers.CharField(max_length=500)
    
    def validate_cliente_id(self, value):
        """Valida que el cliente exista."""
        try:
            Cliente.objects.get(id=value)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("Cliente no encontrado")
        return value


class PagoSerializer(serializers.ModelSerializer):
    """Serializer para pagos."""

    pedido_id = serializers.SerializerMethodField(read_only=True)
    monto = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Pago
        fields = ["id", "pedido_id", "metodo_pago", "monto", "estado"]

    def get_pedido_id(self, obj):
        """Retorna el ID del pedido."""
        return obj.pedido.id
    
    def get_monto(self, obj):
        """Retorna el monto como float."""
        return float(obj.monto)


class EnvioSerializer(serializers.ModelSerializer):
    """Serializer para envíos."""

    pedido_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Envio
        fields = ["id", "pedido_id", "direccion_entrega", "estado_envio"]

    def get_pedido_id(self, obj):
        """Retorna el ID del pedido."""
        return obj.pedido.id


class CompraCompleteSerializer(serializers.Serializer):
    """Serializer para mostrar resumen completo de la compra."""

    pedido = PedidoSerializer()
    pago = PagoSerializer()
    envio = EnvioSerializer()