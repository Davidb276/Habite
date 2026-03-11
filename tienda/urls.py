from django.urls import path
from .views import catalogo
from .api_views import (
    ProductosAPI, 
    ProductoDetalleAPI,
    CrearPedidoAPI,
    PedidoDetalleAPI,
    ClientesAPI,
    CarritoAPI,
    AgregarAlCarritoAPI,
    EliminarDelCarritoAPI,
    VaciarCarritoAPI,
    CheckoutCarritoAPI,
    PagoDetalleAPI,
    EnvioDetalleAPI,
    ActualizarEstadoEnvioAPI
)


urlpatterns = [
    # Vistas tradicionales
    path("", catalogo, name="catalogo"),

    # APIs REST - Productos
    path("api/productos/", ProductosAPI.as_view(), name="api-productos"),
    path("api/productos/<int:producto_id>/", ProductoDetalleAPI.as_view(), name="api-producto-detalle"),
    
    # APIs REST - Pedidos
    path("api/pedidos/", CrearPedidoAPI.as_view(), name="api-crear-pedido"),
    path("api/pedidos/<int:pedido_id>/", PedidoDetalleAPI.as_view(), name="api-pedido-detalle"),
    
    # APIs REST - Clientes
    path("api/clientes/", ClientesAPI.as_view(), name="api-clientes"),
    
    # APIs REST - Carrito
    path("api/carrito/<int:cliente_id>/", CarritoAPI.as_view(), name="api-carrito"),
    path("api/carrito/agregar/", AgregarAlCarritoAPI.as_view(), name="api-agregar-carrito"),
    path("api/carrito/<int:cliente_id>/eliminar/<int:producto_id>/", EliminarDelCarritoAPI.as_view(), name="api-eliminar-carrito"),
    path("api/carrito/<int:cliente_id>/vaciar/", VaciarCarritoAPI.as_view(), name="api-vaciar-carrito"),
    path("api/carrito/checkout/", CheckoutCarritoAPI.as_view(), name="api-checkout-carrito"),
    
    # APIs REST - Pagos
    path("api/pagos/<int:pago_id>/", PagoDetalleAPI.as_view(), name="api-pago-detalle"),
    
    # APIs REST - Envíos
    path("api/envios/<int:envio_id>/", EnvioDetalleAPI.as_view(), name="api-envio-detalle"),
    path("api/envios/<int:envio_id>/actualizar/", ActualizarEstadoEnvioAPI.as_view(), name="api-actualizar-envio"),
]