import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'habite_project.settings')
django.setup()

from tienda.models import Categoria

# Crear las 4 categorías
categorias = [
    {'nombre': 'Textiles', 'slug': 'textiles', 'icono': 'fas fa-layer-group', 'orden': 0},
    {'nombre': 'Decoración', 'slug': 'decoracion', 'icono': 'fas fa-palette', 'orden': 1},
    {'nombre': 'Mobiliario', 'slug': 'mobiliario', 'icono': 'fas fa-chair', 'orden': 2},
    {'nombre': 'Iluminación', 'slug': 'iluminacion', 'icono': 'fas fa-lightbulb', 'orden': 3},
]

print("Creando categorías...")
for cat_data in categorias:
    cat, created = Categoria.objects.get_or_create(**cat_data)
    if created:
        print(f"✓ Categoría '{cat.nombre}' creada")
    else:
        print(f"- Categoría '{cat.nombre}' ya existe")

print("\nCategorías en la base de datos:")
for cat in Categoria.objects.all().order_by('orden'):
    print(f"  • {cat.nombre} ({cat.slug}) - Icono: {cat.icono}")
