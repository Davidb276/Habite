from tienda.domain.builders import PedidoBuilder
from tienda.infra.factories import NotificadorFactory
from tienda.models import Cliente, Producto

class PedidoService:
    def __init__(self):
        self.notificador = NotificadorFactory.crear_notificador()

    def crear_pedido(self, cliente_id, productos_data):
        cliente = Cliente.objects.get(id=cliente_id)

        builder = PedidoBuilder().para_cliente(cliente)

        for prod_id, cantidad in productos_data:
            producto = Producto.objects.get(id=prod_id)
            builder.agregar_item(producto, cantidad)

        pedido = builder.build()
        self.notificador.enviar(pedido)

        return pedido
