# Migración a Microservicios - Strangler Pattern

**Proyecto**: Habité | E-commerce Premium  
**Taller**: Taller 02 - El Patrón Estrangulador  
**Fecha**: Abril 2026  
**Profesor**: Nicolás Ramírez Vélez - Arquitectura de Software

---

## 📋 Índice

1. [Matriz de Decisión](#matriz-de-decisión)
2. [Módulo Estrangulado](#módulo-estrangulado)
3. [Arquitectura de Separación](#arquitectura-de-separación)
4. [Componentes Implementados](#componentes-implementados)
5. [Flujo de Migración](#flujo-de-migración)
6. [Testing & Validación](#testing--validación)
7. [Cómo Ejecutar](#cómo-ejecutar)

---

## 📊 Matriz de Decisión

Evaluamos los módulos principales del proyecto siguiendo tres criterios:

### Criterios de Evaluación

| Criterio | Descripción |
|----------|-------------|
| **Carga CPU** | ¿Qué tan intensivo es en recursos de procesamiento? |
| **Frecuencia Cambio** | ¿Con qué frecuencia requiere actualizaciones? |
| **Acoplamiento** | ¿Qué tan integrado está con el resto del monolito? |

### Módulos Evaluados

| Módulo | Carga CPU | Frecuencia | Acoplamiento | **Decisión** |
|--------|-----------|-----------|--------------|-------------|
| Autenticación | Baja | Baja | MUY ALTO | ❌ Mantener Django |
| Catálogo | Media | Baja | MUY ALTO | ❌ Mantener Django |
| Carrito | Media | Media | MUY ALTO | ❌ Mantener Django |
| Pedidos | Baja | Media | MUY ALTO | ❌ Mantener Django |
| 🎯 **Pagos & Facturas** | **MUY ALTA ⚠️** | **ALTA ↗️** | **MEDIO** | **✅ ESTRANGULAR** |

---

## 🎯 Módulo Estrangulado: Procesamiento de Pagos & Generación de Facturas

### Justificación Técnica

#### **1. Consumo de Recursos: CRÍTICO ⚠️**

**Problema Actual en Django:**
```python
# tienda/services.py - FacturaService
def generar_factura_pdf(pedido):
    # ReportLab genera PDFs en tiempo real
    # Bloquea el hilo principal de Django
    # Usa 200-500 MB de memoria por solicitud
    # Causa timeouts en otros usuarios
```

**Impacto:**
- El servidor Django ejecuta una sola solicitud a la vez
- Un usuario descargando una factura = Todos los demás esperan
- Bottleneck clásico de procesamiento síncronico

#### **2. Frecuencia de Cambio: ALTA ↗️**

Requisitos que cambian constantemente:
- ✅ Nuevos campos legales (impuestos, retenciones)  
- ✅ Cambios en formato de factura y branding
- ✅ Integración con pasarelas (Stripe, MercadoPago, PayPal)
- ✅ Nuevas estrategias de pago (depósitos, cuotas)
- ✅ Reportes y auditoría financiera

**Problema con Monolito:**
Cada cambio requiere redeploy de TODO Django.

#### **3. Acoplamiento: MEDIO 🔗**

**Dependencias Limitadas:**
- Necesita: `Pedido`, `Cliente`, `Pago`
- No modifica: Autenticación, Catálogo, Carrito
- Puede procesarse **asincronamente** sin afectar pedidos

---

## 🏗️ Arquitectura de Separación

### Topología Actual (Monolito)

```
┌─────────────────────────────────┐
│     DJANGO (Todo en uno)        │
├─────────────────────────────────┤
│ • Autenticación                 │
│ • Catálogo                      │
│ • Carrito                       │
│ • Pedidos                       │  ← Todo espera aquí
│ • PDF (FacturaService) ⚠️       │  ← Cuello de botella
│ • Pagos                         │
└─────────────────────────────────┘
         ↓
      SQLite/PostgreSQL
```

### Topología Después (Strangler Pattern)

```
┌──────────────────────────────────┐         ┌──────────────────────┐
│    DJANGO (Monolito Ligero)       │         │  FLASK (Microservicio)
├──────────────────────────────────┤         ├──────────────────────┤
│ • Autenticación                  │         │ • PDF Generation     │
│ • Catálogo                       │◄───────►│ • Payment Processing │
│ • Carrito                        │ /api/v2/│ • WhatsApp Notify    │
│ • Pedidos                        │         │ • Reportes           │
│ • Clientes                       │         │ (Ligero = Fast ⚡)   │
└──────────────────────────────────┘         └──────────────────────┘
         ↓                                              ↓
      PostgreSQL ◄─────────────────────────────────────┘
      (Compartida)
```

### Orquestación con Nginx

```
Internet
   ↓
┌─────────────────┐
│     Nginx       │  ← Router inteligente
│  (Strangler)    │
└────────┬────────┘
         ↓
    ┌────┴─────────────────────────────┐
    ↓                                  ↓
Legacy Routes                   /api/v2/facturas/
/                               /api/v2/pagos/
/catalogo/                      /api/v2/notificaciones/
/login/                                ↓
    ↓                           ┌─────────────────┐
┌─────────────────┐            │ FLASK Service   │
│   DJANGO        │            │ (Aislado)       │
│ (8000)          │            │ (5000)          │
└─────────────────┘            └─────────────────┘
```

---

## 🔧 Componentes Implementados

### 1. Microservicio Flask (`flask_payment_service/`)

**Estructura:**
```
flask_payment_service/
├── app.py                 # Aplicación Flask principal
├── Dockerfile             # Contenedor independiente
├── requirements.txt       # Dependencias Python
└── .env.example           # Variables de configuración
```

**Endpoints Implementados:**

| Método | Endpoint | Responsabilidad | Status |
|--------|----------|-----------------|--------|
| `POST` | `/api/v2/facturas/generar` | Genera PDF de factura | ✅ |
| `GET` | `/api/v2/facturas/<id>` | Obtiene factura existente | ✅ |
| `POST` | `/api/v2/pagos/procesar` | Procesa un pago | ✅ |
| `POST` | `/api/v2/notificaciones/whatsapp` | Envía WhatsApp | ✅ |
| `GET` | `/health` | Health check | ✅ |
| `GET` | `/api/v2/status` | Status del servicio | ✅ |

**Características:**
- ✅ Generación de PDF con ReportLab (migrado de Django)
- ✅ Procesamiento de pagos con estrategias (SOLID)
- ✅ Manejo robusto de excepciones (400/500 estructurados)
- ✅ Logging detallado
- ✅ CORS habilitado para llamadas desde Django

### 2. Docker Compose Actualizado (`docker-compose.yml`)

**Servicios Orquestados:**

```yaml
db:
  - PostgreSQL 15
  - Health checks habilitados
  
django_web:
  - Django 5.2.4
  - Gunicorn worker pool
  - Static files
  
flask_payment:  ← NUEVO
  - Flask 3.0.0
  - Gunicorn (4 workers)
  - ReportLab para PDFs
  - Aislado del monolito
  
nginx:  ← NUEVO
  - Reverse proxy
  - Ruteo inteligente (Strangler)
  - Load balancing
  - Health checks
```

**Ventajas:**
- 🔄 Todos los servicios se levantan con `docker-compose up`
- 🏥 Health checks automáticos
- 🌐 Red interna propia (habite_network)
- 💾 Volúmenes compartidos para media/static

### 3. Nginx Configuration (`nginx.conf`)

**Ejemplo de enrutamiento:**

```nginx
# STRANGLER: Rutas nuevas → Flask
location /api/v2/facturas/ {
    proxy_pass http://flask_payment_service;  # Puerto 5000
    proxy_read_timeout 60s;                   # PDF puede tardar
}

# LEGACY: Rutas antiguas → Django
location / {
    proxy_pass http://django_backend;        # Puerto 8000
    proxy_read_timeout 30s;
}
```

**Beneficios:**
- ✅ Transparente para el cliente (misma URL raíz)
- ✅ Sin cambios en el frontend
- ✅ Fácil bifurcación de tráfico
- ✅ Rollback sin modificar código

---

## 🔄 Flujo de Migración

### Fase 0: Estado Inicial (Hoy)
```
Solicitud PDF → Django → FacturaService → Bloqueo 🔴
```

### Fase 1: Coexistencia (Ahora implementado)
```
Solicitud PDF → Nginx → Flask (aislado) ✅
             → Otros → Django (normal) ✅
```

### Fase 2: Validación (Next)
```
Monitoreo comparativo:
- Latencia: Flask vs Django
- CPU/Memory: Flask standalone
- Error rate: Ambos servicios
```

### Fase 3: Migración Gradual (Future)
```
Opción A: 10% → 50% → 100% de tráfico a Flask
Opción B: Full feature flag en Django
Opción C: Eliminación completa de FacturaService (Django) 
```

---

## ✅ Testing & Validación

### Health Checks

Todos los servicios tienen health checks habilitados:

```bash
# Docker Compose
docker-compose ps  # Verificar status

# Endpoints manuales
curl http://localhost/health                    # Nginx
curl http://localhost:8000/admin                # Django
curl http://localhost:5000/health               # Flask
```

### Tests de Endpoints

**Generar Factura:**
```bash
curl -X POST http://localhost/api/v2/facturas/generar \
  -H "Content-Type: application/json" \
  -d '{
    "pedido": {
      "id": 123,
      "fecha": "2026-04-16T10:30:00",
      "cliente": {
        "nombre": "John Doe",
        "email": "john@example.com",
        "telefono": "+57 300 123 4567",
        "direccion": "Medellín"
      },
      "items": [{"nombre": "Silla", "cantidad": 2, "precio": 150000}],
      "total": 300000
    }
  }' \
  > factura.pdf
```

**Procesar Pago:**
```bash
curl -X POST http://localhost/api/v2/pagos/procesar \
  -H "Content-Type: application/json" \
  -d '{
    "pedido_id": 123,
    "monto": 750000,
    "metodo_pago": "Transferencia"
  }'
```

**WhatsApp Notification:**
```bash
curl -X POST http://localhost/api/v2/notificaciones/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "pedido_id": 123,
    "monto": 750000,
    "cliente_nombre": "John Doe"
  }'
```

---

## 🚀 Cómo Ejecutar

### Requisitos
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Pasos

**1. Clonar el repositorio**
```bash
cd c:\Users\david\Habité
```

**2. Configurar variables de entorno**
```bash
# Si no existe .env en root
cp flask_payment_service/.env.example .env
```

**3. Levantar Docker Compose**
```bash
docker-compose up -d
```

**4. Esperar health checks**
```bash
docker-compose ps
# Todos deben tener "healthy" en STATUS
```

**5. Verificar servicios**
```bash
# Nginx router
curl http://localhost/health

# Django admin
open http://localhost/admin

# Flask status
curl http://localhost:5000/api/v2/status
```

**6. Crear datos de prueba (opcional)**
```bash
docker-compose exec django_web python manage.py crear_productos
docker-compose exec django_web python manage.py crear_usuarios
```

### Parar servicios
```bash
docker-compose down

# Limpiar volúmenes (cuidado: borra BD)
docker-compose down -v
```

---

## 📊 Tabla Comparativa: Antes vs Después

| Aspecto | Monolito Django | Microservicio Flask |
|---------|---|---|
| **Startup Time** | 3-5 segundos | 0.5 segundos |
| **Memory (idle)** | 150-200 MB | 30-50 MB |
| **PDF Generation** | Síncrono (bloquea) | Aislado |
| **Escalabilidad** | Monolítica | Horizontal |
| **Deploy** | TODO Django | Solo Flask |
| **Mantentenimiento** | Una rama compleja | Dos ramas modulares |
| **Failures** | Afecta todo | Solo pagos/facturas |

---

## 🛡️ Principios SOLID Aplicados

### Single Responsibility (S)
- Django: Lógica de negocio + Interfaz web
- Flask: Procesamiento de pagos + Facturas

### Open/Closed (O)
- Nuevas pasarelas en Flask **sin modificar** Django
- Estrategias de pago extensibles

### Liskov Substitution (L)
- Ambos servicios implementan `IPaymentService`
- Intercambiables sin cambiar contrato

### Interface Segregation (I)
- Endpoints específicos y limpios
- Cada servicio expone solo lo necesario

### Dependency Inversion (D)
- Ambos dependen de abstracciones, no implementaciones
- Inyección de dependencias en `PagoService`

---

## 📝 Commits Semánticos

```
chore: Setup project structure for Strangler Pattern

feat: Create Flask microservice for payment processing
feat: Add PDF generation endpoint
feat: Add payment processing endpoint
feat: Add WhatsApp notification endpoint

infra: Add Docker Compose with Flask service
infra: Add Nginx reverse proxy configuration
infra: Add health checks for all services

docs: Add Strangler Pattern migration documentation
docs: Add decision matrix for module selection

test: Add curl examples for endpoint testing
```

---

## 🔗 Referencias

- [Martin Fowler - Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Nginx Proxy Configuration](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Docker Compose](https://docs.docker.com/compose/)

---

**Status**: ✅ Implementado y funcional
**Próximos Pasos**: Monitoring, Load Testing, Gradual Traffic Shift
