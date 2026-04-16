# Matriz de Decisión para Strangler Pattern

**Taller 02: El Patrón Estrangulador**  
**Arquitectura de Software 2026**

---

## 📊 Análisis de Módulos - Habité

| Módulo | Carga CPU | Consumo Memoria | Frecuencia Cambio | Acoplamiento | **Decisión** |
|--------|-----------|-----------------|-------------------|--------------|-------------|
| **Autenticación** | Baja | Baja | Baja | Alto (Auth middleware) | ❌ Mantener en Django |
| **Catálogo de Productos** | Media | Media | Media | Alto (ORM relacions) | ❌ Mantener en Django |
| **Carrito de Compras** | Media | Media | Alta | Muy Alto (DB complejo) | ❌ Mantener en Django |
| **Gestión de Pedidos** | Baja | Baja | Media | Muy Alto (Core entidad) | ❌ Mantener en Django |
| **🎯 Procesamiento de Pagos & Facturas** | **Muy Alta** | **Muy Alta** | **Alta** | **Medio** | **✅ ESTRANGULAR** |

---

## 🎯 Módulo Seleccionado: Procesamiento de Pagos & Generación de Facturas

### Justificación

#### **1. Consumo de Recursos: ⚠️ CRÍTICO**
- **Problema Actual**: El servicio `FacturaService` genera PDFs en tiempo real usando ReportLab
- **Impacto**: Cada generación de factura consume ~200-500MB de memoria temporal
- **Bloqueo**: Las solicitudes de PDF bloquean el hilo principal de Django
- **Síntoma**: Otros usuarios experimentan timeouts durante la descarga de facturas

#### **2. Frecuencia de Cambio: 📈 ALTA**
- Requisitos de facturación cambian frecuentemente:
  - Nuevos campos legales (impuestos, retenciones)
  - Cambios en formato de factura
  - Integración con pasarelas (Stripe, MercadoPago, PayPal)
  - Nuevas estrategias de pago (depósitos, cuotas, etc.)
  
#### **3. Acoplamiento: 🔗 MEDIO**
- Dependencias limitadas (principalmente `Pedido` y `Pago`)
- No es core para operaciones transaccionales
- Puede procesarse de forma independiente y asincrónica

---

## ✅ Solución Propuesta

### **Microservicio Flask: `payment_service`**

```
Habité (Monolito Django)              Flask Payment Service
┌──────────────────────────┐          ┌──────────────────────────┐
│ - Autenticación          │          │ - Generación de PDFs     │
│ - Catálogo               │◄────────►│ - Procesamiento de Pagos │
│ - Carrito                │ /api/v2/ │ - Notificaciones         │
│ - Pedidos                │          │ - WhatsApp Integration   │
│ - Clientes               │          │ - Reportes               │
└──────────────────────────┘          └──────────────────────────┘
```

### **Beneficios Esperados**

| Beneficio | Impacto |
|-----------|---------|
| ⚡ Mayor responsividad | Monolito sin bloqueos de PDF |
| 📈 Escalabilidad | Flask puede replicarse sin replicar Django |
| 🔄 Actualizaciones independientes | Cambios en facturación sin redeploy de Django |
| 🛡️ Aislamiento de fallos | Caída del servicio de pagos ≠ caída del catálogo |
| 💰 Optimización de recursos | Python ligero (Flask) vs Django + ORM |

---

## 🏗️ Arquitectura de Separación

### **Antes (Monolito)**
```
GET /pedidos/<id>/descargar-factura/
    ↓
Django View → FacturaService → ReportLab PDF
    ↓
Bloquea hilo + consume memoria
```

### **Después (Strangler Pattern)**
```
GET /pedidos/<id>/descargar-factura/
    ↓
Django View (sin cambios para usuario)
    ↓
Nginx Router (/api/v2/facturas/ → Flask)
    ↓
Flask Service → Generar PDF (aislado)
    ↓
Respuesta rápida al usuario
```

---

## 🔌 Endpoints del Microservicio

| Método | Ruta | Responsabilidad | Status |
|--------|------|-----------------|--------|
| `POST` | `/api/v2/facturas/generar` | Generar PDF de factura | 🔨 NEW |
| `GET` | `/api/v2/facturas/<pedido_id>` | Obtener factura existente | 🔨 NEW |
| `POST` | `/api/v2/pagos/procesar` | Procesar pago y notificar | 🔨 NEW |
| `POST` | `/api/v2/notificaciones/whatsapp` | Enviar WhatsApp de pago | 🔨 NEW |

---

## 📋 Tabla Comparativa: Monolito vs Microservicio

| Aspecto | Django (Antes) | Flask (Después) |
|--------|---|---|
| **Startup Time** | ~3-5s | ~0.5s |
| **Memory Footprint** | ~150-200MB | ~30-50MB |
| **PDF Generation** | Síncrono (bloquea) | Asíncrono (aislado) |
| **Escalabilidad Horizontal** | Difícil (replicar todo) | Fácil (solo este servicio) |
| **Mantenimiento** | Una rama (complejo) | Dos ramas (modular) |

---

## ✨ Principios SOLID Aplicados

- **S (Single Responsibility)**: Cada servicio tiene un propósito único
  - Django: Lógica de negocio + Interfaz
  - Flask: Procesamiento de pagos + Facturas
  
- **O (Open/Closed)**: Abierto para extensión sin modificar Django
  - Nuevas pasarelas de pago en Flask sin tocar Django
  
- **L (Liskov Substitution)**: Ambos servicios implementan `IPaymentService`

- **I (Interface Segregation)**: Endpoints específicos y limpios

- **D (Dependency Inversion)**: Ambos servicios dependen de abstracciones (estrategias)

---

## 🚀 Plan de Migración

### Fase 1: Setup Infrastructure (Hoy)
- ✅ Crear estructura Flask
- ✅ Implementar endpoints básicos
- ✅ Docker + Docker Compose
- ✅ Nginx routing

### Fase 2: Testing & Validation
- [ ] Tests unitarios Flask
- [ ] Tests de integración (Django ↔ Flask)
- [ ] Load testing con Apache Bench
- [ ] Validación de PDFs generados

### Fase 3: Migración Gradual
- [ ] Redirigir 10% de tráfico a Flask
- [ ] Monitoreo de errores
- [ ] Redirigir 100% cuando estable

---

**Fecha de Decisión**: Abril 2026  
**Status**: ✅ APROBADO - Proceder con implementación
