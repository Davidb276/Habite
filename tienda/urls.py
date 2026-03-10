from django.urls import path
from .views import catalogo
from .api_views import ProductosAPI, CrearPedidoAPI


urlpatterns = [

    path("", catalogo, name="catalogo"),

    path("api/productos/", ProductosAPI.as_view()),
    path("api/pedidos/", CrearPedidoAPI.as_view()),

]