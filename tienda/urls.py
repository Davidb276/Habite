from django.urls import path
from .views import (InicioView, CatalogoView, CategoriasView, LoginView, SignUpView, logout_view, AgregarProductoView, PerfilView, 
                    MisPedidosView, GestionarPedidosView, DetallePedidoUserView, DetallePedidoAdminView, descargar_factura, pagar_ahora)
from .api.api_views import (
    ProductosAPI, 
    ProductoDetalleAPI,
    CrearPedidoAPI,
    PedidoDetalleAPI,
    ClientesAPI,
    MiClienteAPI,
    CarritoAPI,
    AgregarAlCarritoAPI,
    EliminarDelCarritoAPI,
    VaciarCarritoAPI,
    CheckoutCarritoAPI,
    PagoDetalleAPI,
    EnvioDetalleAPI,
    ActualizarEstadoEnvioAPI,
    MisPedidosAPI,
    TodosPedidosAPI,
    ActualizarEstadoPedidoAPI
)


urlpatterns = [
    # Vistas tradicionales (Class-Based Views)
    path("", InicioView.as_view(), name="inicio"),
    path("catalogo/", CatalogoView.as_view(), name="catalogo"),
    path("categorias/", CategoriasView.as_view(), name="categorias"),
    path("login/", LoginView.as_view(), name="login"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("logout/", logout_view, name="logout"),
    path("perfil/", PerfilView.as_view(), name="perfil"),
    path("mis-pedidos/", MisPedidosView.as_view(), name="mis_pedidos"),
    path("mis-pedidos/<int:pedido_id>/", DetallePedidoUserView.as_view(), name="detalle_pedido_usuario"),
    path("gestionar-pedidos/", GestionarPedidosView.as_view(), name="gestionar_pedidos"),
    path("gestionar-pedidos/<int:pedido_id>/", DetallePedidoAdminView.as_view(), name="detalle_pedido_admin"),
    path("agregar-producto/", AgregarProductoView.as_view(), name="agregar_producto"),
    path("pedidos/<int:pedido_id>/descargar-factura/", descargar_factura, name="descargar_factura"),
    path("pedidos/<int:pedido_id>/pagar-ahora/", pagar_ahora, name="pagar_ahora"),

    # APIs REST - Productos
    path("api/productos/", ProductosAPI.as_view(), name="api-productos"),
    path("api/productos/<int:producto_id>/", ProductoDetalleAPI.as_view(), name="api-producto-detalle"),
    
    # APIs REST - Pedidos
    path("api/pedidos/", CrearPedidoAPI.as_view(), name="api-crear-pedido"),
    path("api/pedidos/<int:pedido_id>/", PedidoDetalleAPI.as_view(), name="api-pedido-detalle"),
    path("api/pedidos/<int:pedido_id>/cambiar-estado/", ActualizarEstadoPedidoAPI.as_view(), name="api-cambiar-estado-pedido"),
    
    # APIs REST - Clientes
    path("api/clientes/", ClientesAPI.as_view(), name="api-clientes"),
    path("api/mi-cliente/", MiClienteAPI.as_view(), name="api-mi-cliente"),
    
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