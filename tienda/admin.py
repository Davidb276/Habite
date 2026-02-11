from django.contrib import admin
from .models import *

admin.site.register(Cliente)
admin.site.register(Producto)
admin.site.register(Inventario)
admin.site.register(Carrito)
admin.site.register(Pedido)
admin.site.register(Pago)
admin.site.register(Envio)
