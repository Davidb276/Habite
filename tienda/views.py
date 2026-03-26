from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, FormView
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.http import Http404
from django.db.models import Q
from .models import Producto, Pedido, Pago, Envio, Cliente
from .forms import SignUpForm, PerfilUsuarioForm, PerfilClienteForm


class InicioView(TemplateView):
    """Vista de bienvenida/sobre nosotros - Página principal"""
    template_name = "inicio.html"


class CatalogoView(ListView):
    """Vista de catálogo con todos los productos"""
    model = Producto
    template_name = "catalogo.html"
    context_object_name = "productos"
    
    def get_queryset(self):
        """Obtiene todos los productos ordenados por nombre"""
        return Producto.objects.all().order_by('nombre')


class LoginView(DjangoLoginView):
    """Vista de login personalizada"""
    template_name = "login.html"
    success_url = reverse_lazy("catalogo")
    redirect_authenticated_user = True


class SignUpView(FormView):
    """Vista de registro que crea automáticamente User y Cliente"""
    template_name = "signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("catalogo")
    
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