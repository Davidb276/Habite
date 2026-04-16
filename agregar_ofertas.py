#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'habite_project.settings')
django.setup()

from tienda.models import Producto
from decimal import Decimal

# Obtener algunos productos existentes y marcarlos como en oferta
productos = Producto.objects.all()[:10]

# Agregar descuentos a algunos productos
descuentos = [25, 30, 15, 40, 20, 35]

for i, producto in enumerate(productos[:6]):
    descuento = descuentos[i % len(descuentos)]
    producto.en_oferta = True
    producto.descuento_porcentaje = Decimal(str(descuento))
    producto.save()
    print(f"✓ {producto.nombre} - Descuento: {descuento}%")

print("\n Productos marcados como en oferta exitosamente!")
