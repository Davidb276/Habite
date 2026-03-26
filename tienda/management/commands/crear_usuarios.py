from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tienda.models import Cliente

class Command(BaseCommand):
    help = 'Crea usuarios de ejemplo para HABITÉ'

    def handle(self, *args, **options):
        """Crea 2 usuarios: uno normal y uno superadmin"""
        
        # Usuario normal (cliente)
        if not User.objects.filter(username='cliente').exists():
            user_cliente = User.objects.create_user(
                username='cliente',
                email='cliente@habite.com',
                password='cliente123',
                first_name='Cliente',
                last_name='Normal'
            )
            
            # Crear cliente asociado
            if not Cliente.objects.filter(nombre='Cliente Normal').exists():
                Cliente.objects.create(
                    nombre='Cliente Normal',
                    email='cliente@habite.com',
                    direccion='Calle Principal 123',
                    telefono='+1234567890'
                )
            
            self.stdout.write(self.style.SUCCESS('✅ Usuario cliente creado'))
            self.stdout.write('   Username: cliente')
            self.stdout.write('   Password: cliente123')
        else:
            self.stdout.write('⏭️  Usuario cliente ya existe')
        
        # Superadmin
        if not User.objects.filter(username='admin').exists():
            user_admin = User.objects.create_superuser(
                username='admin',
                email='admin@habite.com',
                password='admin123'
            )
            
            # Crear cliente asociado
            if not Cliente.objects.filter(nombre='Administrador').exists():
                Cliente.objects.create(
                    nombre='Administrador',
                    email='admin@habite.com',
                    direccion='Oficina Central',
                    telefono='+1234567891'
                )
            
            self.stdout.write(self.style.SUCCESS('✅ Usuario superadmin creado'))
            self.stdout.write('   Username: admin')
            self.stdout.write('   Password: admin123')
        else:
            self.stdout.write('⏭️  Usuario admin ya existe')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Usuarios de ejemplo creados exitosamente'))
