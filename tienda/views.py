from django.shortcuts import render
from .models import Producto
from django.views import View
from django.http import JsonResponse
from tienda.services import PedidoService

def catalogo(request):
    productos = Producto.objects.all()
    return render(request, "catalogo.html", {"productos": productos})

from django.views import View
from django.http import JsonResponse
from tienda.services import PedidoService

class CrearPedidoView(View):
    def post(self, request):
        data = request.POST
        cliente_id = data["cliente_id"]

        productos = eval(data["productos"])

        service = PedidoService()
        pedido = service.crear_pedido(cliente_id, productos)

        return JsonResponse({"pedido_id": pedido.id})
