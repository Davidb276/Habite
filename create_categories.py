import os
import django
from pathlib import Path
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'habite_project.settings')
django.setup()

from tienda.models import Categoria

# Crear las 4 categorías con sus imágenes
categorias = [
    {
        'nombre': 'Textiles',
        'slug': 'textiles',
        'icono': 'fas fa-layer-group',
        'orden': 0,
        'imagen': '7123I-lggNL.jpg',
        'descripcion': 'Textiles de alta calidad para decorar tu hogar'
    },
    {
        'nombre': 'Decoración',
        'slug': 'decoracion',
        'icono': 'fas fa-palette',
        'orden': 1,
        'imagen': '5a4858f580c5d955fac0c42fcdb532a4.jpg',
        'descripcion': 'Artículos decorativos para embellecer tu espacio'
    },
    {
        'nombre': 'Mobiliario',
        'slug': 'mobiliario',
        'icono': 'fas fa-chair',
        'orden': 2,
        'imagen': '715lp7gyM9L.jpg',
        'descripcion': 'Muebles modernos y cómodos'
    },
    {
        'nombre': 'Iluminación',
        'slug': 'iluminacion',
        'icono': 'fas fa-lightbulb',
        'orden': 3,
        'imagen': '81R4L14e76L._AC_UF8941000_QL80_.jpg',
        'descripcion': 'Soluciones de iluminación elegantes'
    },
]

base_media_path = Path(__file__).resolve().parent / 'media' / 'categorias'

print("Creando categorías con imágenes...")
for cat_data in categorias:
    # Extraer imagen y descripción
    imagen_filename = cat_data.pop('imagen')
    descripcion = cat_data.pop('descripcion')
    
    # Crear o obtener categoría
    cat, created = Categoria.objects.get_or_create(slug=cat_data['slug'], defaults={**cat_data, 'descripcion': descripcion})
    
    if created:
        print(f"✓ Categoría '{cat.nombre}' creada")
    else:
        print(f"- Categoría '{cat.nombre}' ya existe")
    
    # Asignar imagen si existe y la categoría no tiene imagen
    imagen_path = base_media_path / imagen_filename
    if imagen_path.exists() and not cat.imagen:
        try:
            with open(imagen_path, 'rb') as img_file:
                imagen_content = ContentFile(img_file.read())
                cat.imagen.save(imagen_filename, imagen_content, save=True)
            print(f"  📸 Imagen asignada: {imagen_filename}")
        except Exception as e:
            print(f"  ⚠️  Error al asignar imagen: {e}")
    elif cat.imagen:
        print(f"  ✓ Ya tiene imagen: {cat.imagen.name}")

print("\nCategorías en la base de datos:")
for cat in Categoria.objects.all().order_by('orden'):
    has_image = "📸" if cat.imagen else "❌"
    print(f"  • {cat.nombre} ({cat.slug}) - {has_image}")
