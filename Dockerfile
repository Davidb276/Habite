FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles /app/media

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/admin || exit 1

# Exponer puerto
EXPOSE 8000

# Entrypoint
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn habite_project.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60 --access-logfile - --error-logfile -"]
