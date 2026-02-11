from tienda.models import Pedido, Cliente, Producto, PedidoItem

class PedidoBuilder:
    def __init__(self):
        self.cliente = None
        self.items = []

    def para_cliente(self, cliente):
        self.cliente = cliente
        return self 

    def agregar_item(self, producto, cantidad):
        self.items.append((producto, cantidad))
        return self

    def build(self):
        if not self.cliente:
            raise Exception("Cliente requerido")
        if len(self.items) == 0:
            raise Exception("Pedido sin productos")

        pedido = Pedido.objects.create(cliente=self.cliente)

        for producto, cantidad in self.items:
            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad
            )

        pedido.calcular_total()
        return pedido
