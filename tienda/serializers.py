from rest_framework import serializers
from tienda.models import Producto, Pedido, PedidoItem, Cliente
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
    total = serializers.SerializerMethodField(read_only=True)
    fecha = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Pedido
        fields = ["id", "cliente_id", "total", "estado", "fecha", "items"]
        read_only_fields = ["id", "total", "fecha"]
    
    def get_cliente_id(self, obj):
        """Retorna el ID del cliente."""
        return obj.cliente.id if obj.cliente else None
    
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