from django.db import models
from django.contrib.auth.models import User

# ===================== CATEGORÍA =====================
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True)
    icono = models.CharField(max_length=100, default='fas fa-box', help_text='Ej: fas fa-chair')
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


# ===================== CLIENTE =====================
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre


# ===================== PRODUCTO =====================
class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    es_premium = models.BooleanField(default=True)
    en_oferta = models.BooleanField(default=False)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Porcentaje de descuento (0-100)')

    def __str__(self):
        return self.nombre

    def get_precio_descuento(self):
        """Calcula el precio con descuento"""
        if self.en_oferta and self.descuento_porcentaje > 0:
            descuento = self.precio * (self.descuento_porcentaje / 100)
            return self.precio - descuento
        return self.precio

    def get_descuento_monetario(self):
        """Calcula cuánto se ahorra en dinero"""
        if self.en_oferta and self.descuento_porcentaje > 0:
            return self.precio * (self.descuento_porcentaje / 100)
        return 0


# ===================== INVENTARIO =====================
class Inventario(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name="inventario")
    cantidad_disponible = models.IntegerField()

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad_disponible} disponibles"


# ===================== CARRITO =====================
class Carrito(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name="carrito")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de {self.cliente.nombre}"


class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('carrito', 'producto')

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} en carrito"


# ===================== PEDIDO =====================
class Pedido(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pedidos", null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=50, default="Pendiente")

    def __str__(self):
        return f"Pedido #{self.id}"

class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} en pedido #{self.pedido.id}"

    def get_subtotal(self):
        """Calcula el subtotal del item"""
        return self.producto.precio * self.cantidad

# ===================== PAGO =====================
class Pago(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)
    metodo_pago = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50, default="Pendiente")

    def __str__(self):
        return f"Pago #{self.id} - {self.estado}"


# ===================== ENVIO =====================
class Envio(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)
    direccion_entrega = models.TextField()
    estado_envio = models.CharField(max_length=50, default="Preparando")

    def __str__(self):
        return f"Envío para Pedido #{self.pedido.id} - {self.estado_envio}"
