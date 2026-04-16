from django.contrib import admin
from .models import *

class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'orden']
    list_editable = ['orden']
    prepopulated_fields = {'slug': ('nombre',)}
    fieldsets = (
        ('Información Básica', {'fields': ('nombre', 'slug', 'descripcion')}),
        ('Contenido', {'fields': ('imagen', 'icono')}),
        ('Orden', {'fields': ('orden',)}),
    )

admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Cliente)
admin.site.register(Producto)
admin.site.register(Inventario)
admin.site.register(Carrito)
admin.site.register(Pedido)
admin.site.register(Pago)
admin.site.register(Envio)
