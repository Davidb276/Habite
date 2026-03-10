from tienda.models import Pedido, Cliente, Producto, PedidoItem


class PedidoBuilder:
    """
    Builder Pattern para la creación de Pedidos.
    Garantiza que los pedidos se construyen de forma coherente y válida.
    """
    
    def __init__(self):
        self.cliente = None
        self.items = []

    def para_cliente(self, cliente):
        """Define el cliente del pedido."""
        self.cliente = cliente
        return self

    def agregar_item(self, producto, cantidad):
        """Agrega un producto al pedido."""
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        self.items.append((producto, cantidad))
        return self

    def build(self):
        """Construye y persiste el pedido con sus items."""
        if not self.cliente:
            raise ValueError("Cliente requerido para construir el pedido")
        if len(self.items) == 0:
            raise ValueError("El pedido debe contener al menos un producto")

        # Crear pedido
        pedido = Pedido.objects.create(cliente=self.cliente)

        # Crear items y calcular total
        total = 0
        for producto, cantidad in self.items:
            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad
            )
            total += producto.precio * cantidad

        # Establecer total
        pedido.total = total
        pedido.save()
        
        return pedido
