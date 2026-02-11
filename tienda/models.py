from django.db import models
from django.db import models

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
    es_premium = models.BooleanField(default=True)

    def verificar_disponibilidad(self):
        return self.inventario.cantidad_disponible > 0

    def __str__(self):
        return self.nombre


# ===================== INVENTARIO =====================
class Inventario(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name="inventario")
    cantidad_disponible = models.IntegerField()

    def reducir_stock(self, cantidad):
        if self.cantidad_disponible >= cantidad:
            self.cantidad_disponible -= cantidad
            self.save()


# ===================== CARRITO =====================
class Carrito(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de {self.cliente.nombre}"


# ===================== PEDIDO =====================
class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=50, default="Pendiente")

    def calcular_total(self):
        total = sum(item.producto.precio for item in self.items.all())
        self.total = total
        self.save()
        return total

    def __str__(self):
        return f"Pedido #{self.id}"


# ===================== PAGO =====================
class Pago(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)
    metodo_pago = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50, default="Pendiente")

    def procesar_pago(self):
        self.estado = "Pagado"
        self.save()


# ===================== ENVIO =====================
class Envio(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)
    direccion_entrega = models.TextField()
    estado_envio = models.CharField(max_length=50, default="Preparando")

    def actualizar_estado(self, nuevo_estado):
        self.estado_envio = nuevo_estado
        self.save()
