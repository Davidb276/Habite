# 🛋️ Habité - E-commerce Premium para el Hogar

![Status](https://img.shields.io/badge/status-production-green)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Architecture](https://img.shields.io/badge/architecture-Strangler%20Pattern-brightgreen)

---

## 📋 Descripción

**Habité** es una plataforma e-commerce especializada en artículos premium para el hogar, construida con Django + Flask usando el **Patrón Estrangulador (Strangler Pattern)** para una arquitectura moderna y escalable.

### Versión 2.0: Arquitectura Híbrida (Strangler Pattern)

A partir de **Abril 2026**, Habité implementó el patrón arquitectónico **Strangler Pattern** para evolucionar gradualmente de un monolito Django a una arquitectura de microservicios.

**Módulos estrangulados**:
- Core business: inventario, carrito, pedidos, clientes y envíos
- Procesamiento de pagos & generación de facturas

**Justificación**: separar la lógica de negocio más pesada y dejar Django como capa web y compatibilidad temporal.

---

## 🏗️ Arquitectura

```
┌──────────────────────────────────┐         ┌──────────────────────┐
│    DJANGO (Monolito Ligero)       │         │  FLASK (Microservicio)
┌──────────────────────────────────┐    ┌──────────────────────────────────┐    ┌──────────────────────────────┐
│    DJANGO (Fachada Web)          │    │  FLASK CORE (Business Service)   │    │ FLASK PAYMENT (Billing)      │
├──────────────────────────────────┤    ├──────────────────────────────────┤    ├──────────────────────────────┤
│ • Autenticación                  │◄───►│ • Inventario                     │    │ • Procesamiento de pagos     │
│ • Templates / UI                 │    │ • Carrito                        │◄───►│ • Generación de facturas PDF  │
│ • Admin                          │    │ • Pedidos                        │    │ • WhatsApp / reportes         │
│ • Vistas públicas                │    │ • Clientes                       │    └──────────────────────────────┘
│ • API legacy                     │    │ • Envíos                         │
└──────────────────────────────────┘    └──────────────────────────────────┘
                               ↓                                  ↓
                         Nginx router                    Nginx routes /api/v2/*
---

## ⚡ Características

- ✅ **Dashboard de Administración**: Gestión completa de productos, pedidos y usuarios
- ✅ **Catálogo Dinámico**: Productos con imágenes, categorías y descuentos
- ✅ **Carrito de Compras**: Interfaz intuitiva con actualización en tiempo real
- ✅ **Sistema de Pedidos**: Seguimiento completo del estado de compras
- ✅ **Integración WhatsApp**: Notificaciones automáticas de pagos
- ✅ **Generación de Facturas**: PDFs profesionales (aislado en microservicio)
- ✅ **Registro Automático**: Sistema de registro sin fricción
- ✅ **Principios SOLID**: Código mantenible y extensible

---

## 📁 Estructura del Proyecto

```
Habité/
├── 📄 README.md                              # Este archivo
├── 📄 DECISION_MATRIX.md                     # Matriz de decisión (Strangler)
├── 📄 STRANGLER_PATTERN_MIGRATION.md         # Documentación técnica
├── 📄 SOLID_REFACTORING_GUIDE.md             # Principios SOLID aplicados
├── 📄 SETUP_GUIDE.md                         # Guía de instalación
├── 📄 REGISTRO_AUTOMATICO_DOC.md             # Doc. de registro automático
│
├── 🐍 manage.py                              # Gestor Django
├── docker-compose.yml                        # Orquestación de contenedores
├── nginx.conf                                # Configuración del reverse proxy
├── db.sqlite3                                # Base de datos (desarrollo)
│
├── 📁 habite_project/                        # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── 📁 tienda/                                # App principal Django
│   ├── models.py                             # Modelos (Cliente, Pedido, etc.)
│   ├── views.py                              # Vistas de negocio
│   ├── forms.py                              # Formularios (registro, perfil)
│   ├── services.py                           # Servicios (lógica compleja)
│   ├── urls.py                               # Rutas
│   ├── admin.py                              # Panel de administración
│   ├── 📁 domain/                            # Domain-Driven Design
│   │   ├── builders.py                       # Builder Pattern
│   │   ├── strategies.py                     # Strategy Pattern
│   │   ├── interfaces.py                     # ISP - Segregación de interfaces
│   │   └── exceptions.py                     # Excepciones personalizadas
│   ├── 📁 infra/                             # Infrastructure
│   │   └── factories.py                      # Factory Pattern
│   ├── 📁 api/                               # APIs REST
│   │   ├── api_views.py                      # Endpoints
│   │   └── serializers.py                    # DRF Serializers
│   ├── 📁 management/commands/               # Comandos personalizados
│   │   ├── crear_productos.py
│   │   ├── crear_usuarios.py
│   │   └── crear_inventario.py
│   ├── 📁 templates/                         # Plantillas HTML
│   │   ├── base.html
│   │   ├── inicio.html
│   │   ├── catalogo.html
│   │   ├── carrito.html
│   │   ├── mis_pedidos.html
│   │   ├── detalle_pedido.html
│   │   ├── pagar_ahora.html
│   │   └── ...
│   └── 📁 templatetags/                      # Filtros personalizados
│       └── custom_filters.py
│
├── 📁 flask_payment_service/                 # 🆕 Microservicio Flask
│   ├── app.py                                # Aplicación principal
│   ├── Dockerfile                            # Contenedor Flask
│   ├── requirements.txt                      # Dependencias
│   └── .env.example                          # Variables de entorno
│
├── 📁 media/                                 # Archivos de usuario
│   ├── productos/
│   ├── categorias/
│   ├── bancolombia/
│   └── qr/
│
└── 📁 migrations/                            # Migraciones Django
```

---

## 🚀 Quick Start

### Prerequisitos
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Instalación en 3 pasos

```bash
# 1. Clonar repositorio
git clone <url> && cd Habité

# 2. Levantar servicios (Django + Flask core + Flask pagos + Nginx + BD)
docker-compose up -d

# 3. Crear datos de prueba
docker-compose exec django_web python manage.py crear_usuarios
docker-compose exec django_web python manage.py crear_productos
```

### Acceso

| Servicio | URL | Credenciales |
|----------|-----|---|
| 🌐 Sitio Web | http://localhost | - |
| 📦 Admin | http://localhost/admin | admin / admin123 |
| 🛒 Catálogo | http://localhost/catalogo | - |
| 💳 API | http://localhost/api/v2 | - |
| 🏥 Health | http://localhost/health | - |

---

## 📚 Documentación Técnica

- **[Matriz de Decisión y Strangler Pattern](DECISION_MATRIX.md)**: Justificación del módulo estrangulado
- **[Guía de Migración Detallada](STRANGLER_PATTERN_MIGRATION.md)**: Arquitectura, endpoints, testing
- **[Refactorización SOLID](SOLID_REFACTORING_GUIDE.md)**: Principios aplicados
- **[Setup Inicial](SETUP_GUIDE.md)**: Pasos de configuración
- **[Sistema de Registro](REGISTRO_AUTOMATICO_DOC.md)**: Flujo de onboarding

---

## 🔧 Tecnología Stack

### Backend
- **Django 5.2.4**: Framework web Python
- **Flask 3.0.0**: Microservicio ligero
- **PostgreSQL/SQLite**: Base de datos
- **ReportLab**: Generación de PDFs
- **Django REST Framework**: APIs REST
- **Gunicorn**: WSGI application server

### Frontend
- **Bootstrap 5.3**: Framework CSS responsive
- **Font Awesome 6.4**: Iconografía
- **JavaScript Vanilla**: Interactividad
- **HTML5 & CSS3**: Markup y estilos

### Infrastructure
- **Docker & Docker Compose**: Contenedorización
- **Nginx**: Reverse proxy + Strangler router
- **WhatsApp API**: Notificaciones

---

## 💡 Principios de Diseño

### SOLID
| Principio | Implementación |
|-----------|---|
| **S**: Single Responsibility | Cada servicio tiene un propósito único |
| **O**: Open/Closed | Flask abierto a nuevas pasarelas sin modificar Django |
| **L**: Liskov Substitution | Estrategias de pago intercambiables |
| **I**: Interface Segregation | Interfaces específicas (ICartRepository, ICheckoutService) |
| **D**: Dependency Inversion | Inyección de dependencias en servicios |

### Patrones de Diseño
- **Builder Pattern**: Construcción de pedidos (`PedidoBuilder`)
- **Factory Pattern**: Creación de estrategias de pago (`PaymentStrategyFactory`)
- **Strategy Pattern**: Múltiples métodos de pago sin if/else
- **Strangler Pattern**: Migración gradual de monolito a microservicios

---

## 🔒 Seguridad

- ✅ Validación de entrada en todos los endpoints
- ✅ CSRF protection habilitado
- ✅ Autenticación requerida para operaciones sensibles
- ✅ Separación de roles (cliente / admin)
- ✅ SQLi protection (Django ORM)
- ✅ CORS configurado correctamente

---

## 📊 Performance

| Métrica | Valor |
|---------|-------|
| Startup Time (Django) | ~3-5s |
| Startup Time (Flask) | ~0.5s |
| Memory (idle) | ~180 MB |
| PDF Generation | <5s (isolado) |
| Response Time (API) | <200ms |

---

## 🧪 Testing

```bash
# Crear usuarios y productos de prueba
docker-compose exec django_web python manage.py crear_usuarios
docker-compose exec django_web python manage.py crear_productos

# Tests de endpoints (examples en STRANGLER_PATTERN_MIGRATION.md)
curl http://localhost/api/v2/facturas/generar -X POST ...
```

---

## 📞 Contacto & Soporte

**Email**: dev@habite.example.com  
**WhatsApp**: +57 323 8071236  
**Documentación**: Ver archivos `.md` en raíz

---

## 📜 Licencia

Proyecto académico - Taller 02 Arquitectura de Software 2026

---

**Última actualización**: Abril 2026