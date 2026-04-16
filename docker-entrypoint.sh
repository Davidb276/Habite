#!/bin/bash
set -e

echo "🚀 Iniciando Habité..."

# Aplicar migraciones
echo "📦 Aplicando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "📁 Compilando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear datos iniciales si no existen
echo "🎨 Verificando datos iniciales..."
python manage.py shell << END
from tienda.models import Producto, Categoria

# Si no hay productos, crear automáticamente
if Producto.objects.count() == 0:
    print("✅ Creando categorías y productos iniciales...")
    import subprocess
    subprocess.run(['python', 'manage.py', 'crear_categorias'], check=True)
    subprocess.run(['python', 'manage.py', 'crear_productos'], check=True)
    print("✅ Datos iniciales generados!")
else:
    print("✅ Los datos ya existen, saltando inicialización")
END

# Iniciar Gunicorn
echo "🌐 Iniciando servidor Django..."
exec gunicorn habite_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
