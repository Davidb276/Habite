from django.urls import path
from .views import catalogo
from .api_views import (
    ProductosAPI, 
    ProductoDetalleAPI,
    CrearPedidoAPI,
    PedidoDetalleAPI,
    ClientesAPI
)


urlpatterns = [
    # Vistas tradicionales
    path("", catalogo, name="catalogo"),

    # APIs REST
    path("api/productos/", ProductosAPI.as_view(), name="api-productos"),
    path("api/productos/<int:producto_id>/", ProductoDetalleAPI.as_view(), name="api-producto-detalle"),
    path("api/pedidos/", CrearPedidoAPI.as_view(), name="api-crear-pedido"),
    path("api/pedidos/<int:pedido_id>/", PedidoDetalleAPI.as_view(), name="api-pedido-detalle"),
    path("api/clientes/", ClientesAPI.as_view(), name="api-clientes"),
]