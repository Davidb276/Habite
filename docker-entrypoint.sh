#!/bin/sh
set -e

echo "Starting Habite Django container"

echo "Applying migrations"
python manage.py migrate --noinput

echo "Collecting static files"
python manage.py collectstatic --noinput

echo "Checking initial data"
python manage.py shell <<'END'
from tienda.models import Producto

if Producto.objects.count() == 0:
    print("Creating initial categories and products")
    import subprocess
    subprocess.run(['python', 'create_categories.py'], check=True)
    subprocess.run(['python', 'manage.py', 'crear_productos'], check=True)
    print("Initial data created")
else:
    print("Initial data already exists")
END

echo "Starting Gunicorn"
exec gunicorn habite_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
