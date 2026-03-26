from django.core.management.base import BaseCommand
from tienda.models import Producto, Inventario
from django.core.files.base import ContentFile
from io import BytesIO
import requests
from PIL import Image

class Command(BaseCommand):
    help = 'Crea productos de ejemplo para HABITÉ'

    def handle(self, *args, **options):
        """Crea productos de ejemplo"""
        
        productos_data = [
            {
                "nombre": "Lámpara de Pie Dorada",
                "precio": 89.99,
                "categoria": "Iluminación",
                "descripcion": "Elegante lámpara de pie con base de mármol y pantalla textil dorada. Perfecta para crear ambientes cálidos.",
                "stock": 15,
                "emoji": "💡"
            },
            {
                "nombre": "Sillón Moderno Gris",
                "precio": 249.99,
                "categoria": "Mobiliario",
                "descripcion": "Sillón ergonómico en tela gris oscuro con estructura de madera. Ideal para sala o sala de lectura.",
                "stock": 8,
                "emoji": "🪑"
            },
            {
                "nombre": "Cojines de Lino Natural",
                "precio": 34.99,
                "categoria": "Textiles",
                "descripcion": "Set de 2 cojines en lino natural. Añade confort y textura a tu sofá o cama.",
                "stock": 25,
                "emoji": "🛋️"
            },
            {
                "nombre": "Espejo Ornamental Dorado",
                "precio": 129.99,
                "categoria": "Decoración",
                "descripcion": "Espejo circular con marco dorado cepillado. Amplifica la luz natural y añade elegancia.",
                "stock": 12,
                "emoji": "🪞"
            },
            {
                "nombre": "Mesa de Centro Roble",
                "precio": 199.99,
                "categoria": "Mobiliario",
                "descripcion": "Mesa de centro fabricada en roble macizo con acabado natural. Dimensiones: 100x60x45cm.",
                "stock": 6,
                "emoji": "🛏️"
            },
            {
                "nombre": "Cortinas de Terciopelo Beige",
                "precio": 79.99,
                "categoria": "Textiles",
                "descripcion": "Par de cortinas en terciopelo premium. Proporciona privacidad y aislamiento térmico.",
                "stock": 10,
                "emoji": "🪟"
            },
            {
                "nombre": "Jarrón de Cerámica",
                "precio": 49.99,
                "categoria": "Decoración",
                "descripcion": "Jarrón artesanal de cerámica con acabado mate. Perfecto para flores secas o como pieza decorativa.",
                "stock": 18,
                "emoji": "🏺"
            },
            {
                "nombre": "Estantería Modular",
                "precio": 179.99,
                "categoria": "Mobiliario",
                "descripcion": "Sistema de estantería modular en madera y hierro. Adapta tu espacio con elementos reconfigurables.",
                "stock": 7,
                "emoji": "📚"
            },
            {
                "nombre": "Frazada de Algodón Orgánico",
                "precio": 59.99,
                "categoria": "Textiles",
                "descripcion": "Frazada cálida de algodón 100% orgánico. Suave y transpirable para todas las estaciones.",
                "stock": 20,
                "emoji": "🛏️"
            },
            {
                "nombre": "Lámpara Colgante Moderna",
                "precio": 119.99,
                "categoria": "Iluminación",
                "descripcion": "Lámpara colgante de diseño minimalista. Estructura de acero negro con difusor de vidrio.",
                "stock": 11,
                "emoji": "💡"
            },
            {
                "nombre": "Alfombra Jute Tejida",
                "precio": 99.99,
                "categoria": "Textiles",
                "descripcion": "Alfombra natural de jute tejido a mano. Añade warmth y textura a cualquier habitación.",
                "stock": 14,
                "emoji": "🟤"
            },
            {
                "nombre": "Sofá Corner Lino Crema",
                "precio": 599.99,
                "categoria": "Mobiliario",
                "descripcion": "Sofá esquinero en lino crema de alta calidad. Diseño moderno con patas de madera. Muy cómodo.",
                "stock": 4,
                "emoji": "🛋️"
            }
        ]

        for prod_data in productos_data:
            # Verificar si el producto ya existe
            if Producto.objects.filter(nombre=prod_data["nombre"]).exists():
                self.stdout.write(f"⏭️  {prod_data['nombre']} ya existe")
                continue
            
            # Crear producto
            producto = Producto.objects.create(
                nombre=prod_data["nombre"],
                precio=prod_data["precio"],
                categoria=prod_data["categoria"],
                descripcion=prod_data["descripcion"],
                es_premium=True
            )
            
            # Crear inventario
            Inventario.objects.create(
                producto=producto,
                cantidad_disponible=prod_data["stock"]
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ {prod_data['nombre']} creado"))

        self.stdout.write(self.style.SUCCESS("\n🎉 Productos de ejemplo creados exitosamente"))
