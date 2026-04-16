import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'habite_project.settings')
django.setup()

from tienda.models import Producto

print("PRODUCTOS ACTUALES:\n")
for p in Producto.objects.all():
    print(f"ID: {p.id} | {p.nombre} | Precio: ${p.precio}")
