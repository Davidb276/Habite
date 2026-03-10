"""
Comando para inicializar datos de prueba en la base de datos.
Mantiene SOLID: solo crea datos, sin lógica de negocio.
"""

from django.core.management.base import BaseCommand
from tienda.models import Cliente, Producto, Inventario


class Command(BaseCommand):
    help = 'Inicializa datos de prueba en la base de datos'

    def handle(self, *args, **options):
        # Crear cliente de prueba
        cliente, created = Cliente.objects.get_or_create(
            id=1,
            defaults={
                'nombre': 'Juan Cliente',
                'email': 'juan@example.com',
                'direccion': 'Cra 10 #20-30, Bogotá',
                'telefono': '3001234567'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Cliente creado: {cliente.nombre}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✓ Cliente ya existe: {cliente.nombre}')
            )

        # Crear productos
        productos_data = [
            {
                'id': 1,
                'nombre': 'Lámpara LED Moderna',
                'precio': 45.99,
                'categoria': 'Iluminación',
                'descripcion': 'Lámpara LED moderna con control de intensidad y temperatura de color.'
            },
            {
                'id': 2,
                'nombre': 'Cojín Decorativo',
                'precio': 28.50,
                'categoria': 'Textiles',
                'descripcion': 'Cojín de lino con diseño geométrico moderno.'
            },
            {
                'id': 3,
                'nombre': 'Espejo de Pared',
                'precio': 89.99,
                'categoria': 'Decoración',
                'descripcion': 'Espejo de pared con marco de madera de roble.'
            },
            {
                'id': 4,
                'nombre': 'Sofá Gris Claro',
                'precio': 599.00,
                'categoria': 'Mobiliario',
                'descripcion': 'Sofá modular de 3 cuerpos en tela lino.'
            },
            {
                'id': 5,
                'nombre': 'Cortina Premium',
                'precio': 125.00,
                'categoria': 'Textiles',
                'descripcion': 'Cortina de terciopelo con aislante térmico.'
            },
            {
                'id': 6,
                'nombre': 'Florero Cerámica',
                'precio': 35.75,
                'categoria': 'Decoración',
                'descripcion': 'Florero en cerámica artesanal color beige.'
            },
            {
                'id': 7,
                'nombre': 'Estantería Modular',
                'precio': 199.99,
                'categoria': 'Mobiliario',
                'descripcion': 'Estantería de madera con diseño nórdico.'
            },
            {
                'id': 8,
                'nombre': 'Set de Almohadas',
                'precio': 65.00,
                'categoria': 'Textiles',
                'descripcion': 'Set de 4 almohadas de algodón orgánico.'
            },
        ]

        for prod_data in productos_data:
            producto, created = Producto.objects.get_or_create(
                id=prod_data['id'],
                defaults={
                    'nombre': prod_data['nombre'],
                    'precio': prod_data['precio'],
                    'categoria': prod_data['categoria'],
                    'descripcion': prod_data['descripcion'],
                    'es_premium': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Producto creado: {producto.nombre}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'✓ Producto ya existe: {producto.nombre}')
                )

            # Crear inventario para el producto
            inventario, inv_created = Inventario.objects.get_or_create(
                producto=producto,
                defaults={'cantidad_disponible': 50}
            )
            
            if inv_created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Inventario creado: {inventario.cantidad_disponible} unidades'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS('\n✓ Base de datos inicializada correctamente')
        )
