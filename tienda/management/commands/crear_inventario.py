from django.core.management.base import BaseCommand
from tienda.models import Producto, Inventario


class Command(BaseCommand):
    help = 'Crea inventario por defecto para productos sin stock'

    def handle(self, *args, **options):
        productos = Producto.objects.all()
        creados = 0
        
        for producto in productos:
            inventario, created = Inventario.objects.get_or_create(
                producto=producto,
                defaults={'cantidad_disponible': 100}
            )
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Creado inventario para {producto.nombre}: 100 unidades'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total creados: {creados} inventarios')
        )
