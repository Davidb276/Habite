import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'habite_project.settings')
django.setup()

from tienda.models import Producto
from decimal import Decimal

# Tasa de cambio USD a COP
TASA_CAMBIO = Decimal('4200')

print("ACTUALIZANDO PRECIOS DE USD A COP...\n")

for p in Producto.objects.all():
    precio_usd = p.precio
    precio_cop = (precio_usd * TASA_CAMBIO).quantize(Decimal('1'))
    
    print(f"ID: {p.id} | {p.nombre}")
    print(f"  USD: ${precio_usd} → COP: ${precio_cop:,}")
    
    p.precio = precio_cop
    p.save()

print("\n✓ TODOS LOS PRECIOS ACTUALIZADOS A COP")
