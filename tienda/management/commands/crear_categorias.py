from django.core.management.base import BaseCommand
from tienda.models import Categoria
from django.core.files.base import ContentFile
from pathlib import Path
import os

class Command(BaseCommand):
    help = 'Crea categorías de ejemplo para HABITÉ con sus imágenes'

    def handle(self, *args, **options):
        """Crea categorías con imágenes"""
        
        # Mapeo de categorías a sus archivos de imagen
        # Las imágenes ya existen en /media/categorias/
        categorias_data = [
            {
                "nombre": "Textiles",
                "slug": "textiles",
                "descripcion": "Textiles de alta calidad para decorar tu hogar",
                "icono": "fas fa-scroll",
                "imagen": "7123I-lggNL.jpg",
                "orden": 1
            },
            {
                "nombre": "Decoración",
                "slug": "decoracion",
                "descripcion": "Artículos decorativos para embellecer tu espacio",
                "icono": "fas fa-palette",
                "imagen": "5a4858f580c5d955fac0c42fcdb532a4.jpg",
                "orden": 2
            },
            {
                "nombre": "Mobiliario",
                "slug": "mobiliario",
                "descripcion": "Muebles modernos y cómodos",
                "icono": "fas fa-chair",
                "imagen": "715lp7gyM9L.jpg",
                "orden": 3
            },
            {
                "nombre": "Iluminación",
                "slug": "iluminacion",
                "descripcion": "Soluciones de iluminación elegantes",
                "icono": "fas fa-lightbulb",
                "imagen": "81R4L14e76L._AC_UF8941000_QL80_.jpg",
                "orden": 4
            }
        ]

        base_media_path = Path(__file__).resolve().parent.parent.parent.parent / 'media' / 'categorias'

        for cat_data in categorias_data:
            # Verificar si la categoría ya existe
            categoria, created = Categoria.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={
                    "nombre": cat_data["nombre"],
                    "descripcion": cat_data["descripcion"],
                    "icono": cat_data["icono"],
                    "orden": cat_data["orden"]
                }
            )

            # Asignar imagen si existe el archivo
            imagen_path = base_media_path / cat_data["imagen"]
            if imagen_path.exists() and not categoria.imagen:
                try:
                    with open(imagen_path, 'rb') as img_file:
                        imagen_content = ContentFile(img_file.read())
                        categoria.imagen.save(cat_data["imagen"], imagen_content, save=True)
                    self.stdout.write(self.style.SUCCESS(f"✅ {cat_data['nombre']} creado con imagen"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⚠️  {cat_data['nombre']} creado sin imagen: {e}"))
            elif created:
                self.stdout.write(self.style.SUCCESS(f"✅ {cat_data['nombre']} creado (sin imagen)"))
            else:
                self.stdout.write(f"⏭️  {cat_data['nombre']} ya existe")

        self.stdout.write(self.style.SUCCESS("\n🎉 Categorías cargadas exitosamente"))
