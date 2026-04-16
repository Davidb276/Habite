from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, FormView
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse, FileResponse
from django.db.models import Q
from .models import Producto, Pedido, Pago, Envio, Cliente, Categoria
from .forms import SignUpForm, PerfilUsuarioForm, PerfilClienteForm


class InicioView(TemplateView):
    """Vista de bienvenida/sobre nosotros - Página principal"""
    template_name = "inicio.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        context['ofertas'] = Producto.objects.filter(en_oferta=True).order_by('-descuento_porcentaje')[:6]
        return context


class CategoriasView(TemplateView):
    """Vista de categorías principales"""
    template_name = "categorias.html"


class CatalogoView(ListView):
    """Vista de catálogo con filtrado por categoría y ofertas"""
    model = Producto
    template_name = "catalogo.html"
    context_object_name = "productos"
    paginate_by = 12
    
    def get_queryset(self):
        """Obtiene productos, opcionalmente filtrados por categoría u ofertas"""
        queryset = Producto.objects.all().order_by('nombre')
        
        # Filtrar por ofertas si se proporciona en query string
        mostrar_ofertas = self.request.GET.get('ofertas')
        if mostrar_ofertas == 'true':
            queryset = queryset.filter(en_oferta=True)
        
        # Filtrar por categoría si se proporciona en query string
        categoria_slug = self.request.GET.get('categoria')
        if categoria_slug:
            # Buscar la categoría por slug
            try:
                categoria = Categoria.objects.get(slug=categoria_slug)
                # Filtrar productos que coincidan con el nombre de la categoría
                queryset = queryset.filter(categoria__icontains=categoria.nombre)
            except Categoria.DoesNotExist:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Agregar la categoría seleccionada al contexto"""
        context = super().get_context_data(**kwargs)
        categoria_slug = self.request.GET.get('categoria')
        mostrar_ofertas = self.request.GET.get('ofertas')
        
        if mostrar_ofertas == 'true':
            context['titulo_catalogo'] = "Ofertas Disponibles"
        elif categoria_slug:
            try:
                context['categoria_seleccionada'] = Categoria.objects.get(slug=categoria_slug)
                context['titulo_catalogo'] = f"Catálogo - {context['categoria_seleccionada'].nombre}"
            except Categoria.DoesNotExist:
                context['titulo_catalogo'] = "Catálogo"
        else:
            context['titulo_catalogo'] = "Catálogo"
        
        return context


class LoginView(DjangoLoginView):
    """Vista de login personalizada - redirige a la página anterior o a inicio"""
    template_name = "login.html"
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirige a la página 'next' si existe, si no a inicio"""
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy("inicio")


class SignUpView(FormView):
    """Vista de registro que crea automáticamente User y Cliente"""
    template_name = "signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("inicio")
    
    def dispatch(self, request, *args, **kwargs):
        """Redirige al catálogo si el usuario ya está autenticado"""
        if request.user.is_authenticated:
            return redirect('catalogo')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """
        Guarda el formulario, loguea al usuario y redirige al catálogo.
        El formulario automáticamente crea:
        - User (Django)
        - Cliente (modelo personalizado)
        - Carrito (vacío para el nuevo cliente)
        """
        user = form.save()
        # Loguear automáticamente tras registro exitoso
        login(self.request, user)
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        """Añade información al contexto del template"""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Cuenta'
        context['form_subtitle'] = 'Únete a HABITÉ y comienza a comprar'
        return context


@login_required(login_url='login')
def logout_view(request):
    """Vista de logout que cierra sesión y redirige a inicio"""
    logout(request)
    return redirect('inicio')


def es_superadmin(user):
    """Verifica si el usuario es superadmin"""
    return user.is_superuser


@method_decorator(login_required(login_url='login'), name='dispatch')
@method_decorator(user_passes_test(es_superadmin, login_url='catalogo'), name='dispatch')
class AgregarProductoView(CreateView):
    """Vista para que el admin agregue nuevos productos"""
    model = Producto
    template_name = "admin_agregar_producto.html"
    fields = ['nombre', 'precio', 'categoria', 'descripcion', 'imagen']
    success_url = reverse_lazy("catalogo")
    
    def form_valid(self, form):
        """Guarda el producto solo si el usuario es superadmin"""
        response = super().form_valid(form)
        return response


@method_decorator(login_required(login_url='login'), name='dispatch')
class PerfilView(FormView):
    """Vista para que el usuario vea y edite su perfil y datos del cliente"""
    template_name = "perfil.html"
    form_class = PerfilUsuarioForm
    success_url = reverse_lazy("perfil")
    
    def get_context_data(self, **kwargs):
        """Prepara ambos forms para el template"""
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        cliente = get_object_or_404(Cliente, email=current_user.email)
        
        if self.request.POST:
            # Si es un POST, los forms ya están contenidos en kwargs['form']
            context['usuario_form'] = self.get_form()
            context['cliente_form'] = PerfilClienteForm(self.request.POST, instance=cliente)
        else:
            # Si es GET, inicializamos los forms con los datos actuales
            context['usuario_form'] = PerfilUsuarioForm(instance=current_user)
            context['cliente_form'] = PerfilClienteForm(instance=cliente)
        
        return context
    
    def get_form_kwargs(self):
        """Prepara los kwargs para inicializar el form de usuario"""
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Guarda ambos forms (usuario y cliente)"""
        # Guardar el formulario del usuario
        form.save()
        
        # Guardar el formulario del cliente
        cliente = get_object_or_404(Cliente, email=self.request.user.email)
        cliente_form = PerfilClienteForm(self.request.POST, instance=cliente)
        
        if cliente_form.is_valid():
            cliente_form.save()
            return redirect(self.success_url)
        
        # Si el cliente form no es válido, volver a mostrar el formulario
        return self.form_invalid(form)


@method_decorator(login_required(login_url='login'), name='dispatch')
class MisPedidosView(ListView):
    """Vista para que el usuario vea sus pedidos"""
    model = Pedido
    template_name = "mis_pedidos.html"
    context_object_name = "pedidos"
    paginate_by = 10
    
    def get_queryset(self):
        """Obtiene pedidos del usuario actual, con fallback por email para pedidos antiguos"""
        usuario = self.request.user
        return (
            Pedido.objects.filter(
                Q(usuario=usuario) |
                Q(usuario__isnull=True, cliente__email=usuario.email)
            )
            .order_by('-fecha')
        )


@method_decorator(login_required(login_url='login'), name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_superuser, login_url='catalogo'), name='dispatch')
@method_decorator(user_passes_test(lambda user: user.is_superuser, login_url='login'), name='dispatch')
class GestionarPedidosView(ListView):
    """Vista para que el admin vea todos los pedidos"""
    model = Pedido
    template_name = "gestionar_pedidos.html"
    context_object_name = "pedidos"
    paginate_by = 20
    
    def get_queryset(self):
        """Obtiene todos los pedidos y permite filtrar por estado"""
        queryset = Pedido.objects.all().order_by('-fecha')
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


@method_decorator(login_required(login_url='login'), name='dispatch')
class DetallePedidoUserView(DetailView):
    """Vista para que el usuario vea los detalles de su pedido"""
    model = Pedido
    template_name = "detalle_pedido.html"
    context_object_name = "pedido"
    
    def get_object(self):
        """Obtiene el pedido solo si pertenece al usuario autenticado"""
        pedido = get_object_or_404(Pedido, id=self.kwargs['pedido_id'])
        if pedido.usuario != self.request.user:
            raise Http404("No tienes acceso a este pedido")
        return pedido
    
    def get_context_data(self, **kwargs):
        """Añade información adicional al contexto"""
        context = super().get_context_data(**kwargs)
        context['pago'] = Pago.objects.filter(pedido=self.object).first()
        context['envio'] = Envio.objects.filter(pedido=self.object).first()
        return context


@method_decorator(login_required(login_url='login'), name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_superuser, login_url='catalogo'), name='dispatch')
class DetallePedidoAdminView(DetailView):
    """Vista para que el admin vea los detalles de cualquier pedido"""
    model = Pedido
    template_name = "detalle_pedido.html"
    context_object_name = "pedido"
    
    def get_object(self):
        """Obtiene el pedido por ID"""
        return get_object_or_404(Pedido, id=self.kwargs['pedido_id'])
    
    def get_context_data(self, **kwargs):
        """Añade información adicional al contexto"""
        context = super().get_context_data(**kwargs)
        context['pago'] = Pago.objects.filter(pedido=self.object).first()
        context['envio'] = Envio.objects.filter(pedido=self.object).first()
        return context


@login_required(login_url='login')
def descargar_factura(request, pedido_id):
    """Vista para descargar la factura en PDF de un pedido - Usa Flask como primary, Django como fallback"""
    import requests
    from .services import FacturaService
    
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar que el usuario sea el propietario del pedido o admin
    if request.user != pedido.usuario and not request.user.is_superuser:
        raise Http404("No tienes acceso a esta factura")
    
    # Intenta usar Flask primero
    try:
        # Preparar datos del pedido para Flask
        pedido_data = {
            'pedido': {
                'id': pedido.id,
                'fecha': pedido.fecha.isoformat() if pedido.fecha else '',
                'cliente_nombre': f"{pedido.usuario.first_name} {pedido.usuario.last_name}".strip() or pedido.usuario.username,
                'cliente_email': pedido.usuario.email,
                'cliente_telefono': pedido.cliente.telefono if pedido.cliente else '',
                'cliente_direccion': pedido.cliente.direccion if pedido.cliente else '',
                'total': float(pedido.total),
                'items': [
                    {
                        'nombre': item.producto.nombre,
                        'cantidad': item.cantidad,
                        'precio_unitario': float(item.precio_unitario),
                        'subtotal': float(item.cantidad * item.precio_unitario)
                    }
                    for item in pedido.pedidoitem_set.all()
                ]
            }
        }
        
        # Llamar a Flask - usa localhost para trabajar dentro de Docker
        response = requests.post(
            'http://flask_payment:5000/api/v2/facturas/generar',
            json=pedido_data,
            timeout=30
        )
        
        if response.status_code == 200:
            # Retornar el PDF generado por Flask
            pdf_response = FileResponse(
                response.content,
                as_attachment=True,
                filename=f'factura_pedido_{pedido.id}.pdf'
            )
            pdf_response['Content-Type'] = 'application/pdf'
            return pdf_response
    except Exception as e:
        # Si hay error con Flask, registrarlo pero continuar con fallback
        import logging
        logging.debug(f"Error llamando a Flask: {str(e)}")
    
    # Fallback: Generar PDF localmente en Django
    try:
        pdf_buffer = FacturaService.generar_factura_pdf(pedido)
        response = FileResponse(pdf_buffer, as_attachment=True, filename=f'factura_pedido_{pedido.id}.pdf')
        response['Content-Type'] = 'application/pdf'
        return response
    except Exception as e:
        raise Http404(f"Error generando factura: {str(e)}")


@login_required(login_url='login')
def pagar_ahora(request, pedido_id):
    """Vista que genera la factura y abre WhatsApp para pagar"""
    from .services import FacturaService
    
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar que el usuario sea el propietario del pedido
    if request.user != pedido.usuario and not request.user.is_superuser:
        raise Http404("No tienes acceso a este pedido")
    
    # Generar PDF solo para verificar que funciona
    pdf_buffer = FacturaService.generar_factura_pdf(pedido)
    
    # Mensaje para WhatsApp mejorado
    mensaje = f"Hola HABITÉ, ya realicé la transferencia por Bancolombia del pedido #{pedido.id} por ${pedido.total:,.0f} COP. Le adjunto el comprobante de pago. Gracias 🙏"
    
    # Número de WhatsApp (el número de HABITÉ)
    numero_whatsapp = "573238071236"
    
    # Encoding para URL
    from urllib.parse import quote
    mensaje_encoded = quote(mensaje)
    
    # Construir URL de WhatsApp
    url_whatsapp = f"https://wa.me/{numero_whatsapp}?text={mensaje_encoded}"
    
    # Retornar contexto
    context = {
        'pedido': pedido,
        'url_whatsapp': url_whatsapp,
        'pedido_id': pedido_id,
        'cliente_id': pedido.cliente.id,
    }
    
    return render(request, 'pagar_ahora.html', context)