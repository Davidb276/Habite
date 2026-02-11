from django.urls import path
from .views import catalogo
from .views import CrearPedidoView

urlpatterns = [
    path("", catalogo, name="catalogo"),
    path("crear-pedido/", CrearPedidoView.as_view()),
]
