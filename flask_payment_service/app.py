"""
Microservicio Flask: Payment & Invoice Service
Part of Habité - Strangler Pattern Implementation

Responsabilidades:
- Generación de facturas PDF (aislado del monolito)
- Procesamiento de pagos
- Notificaciones WhatsApp
- Reportes de transacciones
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from io import BytesIO
from datetime import datetime
import os
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ==================== CONFIGURACIÓN ====================

class Config:
    """Configuración del microservicio"""
    ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = ENV == 'development'
    WHOAMI = os.getenv('MICROSERVICE_NAME', 'Payment Service')
    VERSION = '1.0.0'
    DJANGO_URL = os.getenv('DJANGO_URL', 'http://django:8000')


app.config.from_object(Config)

# ==================== EXCEPCIONES PERSONALIZADAS ====================

class PaymentServiceError(Exception):
    """Excepción base del servicio de pagos"""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class PedidoNoEncontrado(PaymentServiceError):
    def __init__(self):
        super().__init__("Pedido no encontrado", 404)


class DatosInvalidosError(PaymentServiceError):
    def __init__(self, campo):
        super().__init__(f"Dato inválido: {campo}", 400)


class PDFGenerationError(PaymentServiceError):
    def __init__(self):
        super().__init__("Error generando PDF", 500)


class WhatsAppNotificationError(PaymentServiceError):
    def __init__(self):
        super().__init__("Error enviando notificación WhatsApp", 500)


# ==================== SERVICIO DE FACTURAS ====================

class FacturaService:
    """Generador de facturas en PDF (migrations from Django FacturaService)"""
    
    @staticmethod
    def generar_factura_pdf(pedido_data):
        """
        Genera una factura PDF a partir de los datos del pedido.
        
        Args:
            pedido_data: Dict con estructura:
                {
                    'id': int,
                    'fecha': str (ISO format),
                    'cliente': {'nombre', 'email', 'telefono', 'direccion'},
                    'items': [{'nombre', 'cantidad', 'precio'}],
                    'total': float
                }
        
        Returns:
            BytesIO con contenido PDF
            
        Raises:
            PDFGenerationError: Si hay error en generación
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Estilos personalizados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#0f3d1f'),
                spaceAfter=30,
                alignment=1  # Centrado
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#0f3d1f'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Título
            elements.append(Paragraph("FACTURA", title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Info de HABITÉ
            elements.append(Paragraph("<b>HABITÉ</b> - Artículos Premium para el Hogar", styles['Normal']))
            elements.append(Paragraph("WhatsApp: +57 323 8071236", styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # Info del pedido
            data_pedido = [
                ['Número de Pedido:', f"#{pedido_data['id']}"],
                ['Fecha:', pedido_data.get('fecha', datetime.now().strftime('%d/%m/%Y %H:%M'))],
            ]
            
            tabla_pedido = Table(data_pedido, colWidths=[2*inch, 3*inch])
            tabla_pedido.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ebe5d8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f6f2')]),
            ]))
            
            elements.append(tabla_pedido)
            elements.append(Spacer(1, 0.3*inch))
            
            # Datos del cliente
            cliente = pedido_data.get('cliente', {})
            elements.append(Paragraph("<b>Datos de Envío</b>", heading_style))
            elements.append(Paragraph(f"<b>Cliente:</b> {cliente.get('nombre', 'N/A')}", styles['Normal']))
            elements.append(Paragraph(f"<b>Email:</b> {cliente.get('email', 'N/A')}", styles['Normal']))
            elements.append(Paragraph(f"<b>Teléfono:</b> {cliente.get('telefono', 'N/A')}", styles['Normal']))
            elements.append(Paragraph(f"<b>Dirección:</b> {cliente.get('direccion', 'N/A')}", styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # Items del pedido
            elements.append(Paragraph("<b>Detalles del Pedido</b>", heading_style))
            
            items_data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
            total_items = 0
            
            for item in pedido_data.get('items', []):
                subtotal = float(item.get('precio', 0)) * item.get('cantidad', 0)
                total_items += subtotal
                items_data.append([
                    item.get('nombre', 'N/A'),
                    str(item.get('cantidad', 0)),
                    f"${float(item.get('precio', 0)):,.2f}",
                    f"${subtotal:,.2f}"
                ])
            
            items_data.append(['', '', 'TOTAL:', f"${pedido_data.get('total', total_items):,.2f}"])
            
            tabla_items = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
            tabla_items.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -2), 'Helvetica', 9),
                ('FONT', (0, -1), (-1, -1), 'Helvetica', 11),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3d1f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -2), 1, colors.grey),
                ('GRID', (0, -1), (-1, -1), 1, colors.HexColor('#0f3d1f')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f6f2')]),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ebe5d8')),
            ]))
            
            elements.append(tabla_items)
            elements.append(Spacer(1, 0.4*inch))
            
            # Mensaje de pago
            elements.append(Paragraph(
                "<b>Para completar tu pedido, realiza una transferencia bancaria al número de WhatsApp anterior.</b>",
                ParagraphStyle(
                    'InfoPago',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#0f3d1f'),
                    alignment=1
                )
            ))
            
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(
                "¡Gracias por tu compra en HABITÉ!",
                ParagraphStyle(
                    'Footer',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=colors.grey,
                    alignment=1
                )
            ))
            
            # Generar PDF
            doc.build(elements)
            pdf_buffer.seek(0)
            
            logger.info(f"✅ Factura generada exitosamente (Pedido #{pedido_data['id']})")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"❌ Error generando PDF: {str(e)}")
            raise PDFGenerationError()


# ==================== SERVICIO DE PAGOS ====================

class PagoService:
    """Gestor de pagos y notificaciones"""
    
    WHATSAPP_API_URL = "https://api.whatsapp.com/send"  # Mock
    WHATSAPP_NUMBER = "573238071236"
    
    @staticmethod
    def procesar_pago(pago_data):
        """
        Procesa un pago.
        
        Args:
            pago_data: Dict con {pedido_id, monto, metodo_pago}
            
        Returns:
            Dict con resultado del pago
        """
        try:
            pedido_id = pago_data.get('pedido_id')
            monto = pago_data.get('monto')
            metodo = pago_data.get('metodo_pago', 'Transferencia')
            
            if not pedido_id or not monto:
                raise DatosInvalidosError("pedido_id o monto")
            
            # Mock: Simular procesamiento
            resultado = {
                'pedido_id': pedido_id,
                'monto': monto,
                'metodo': metodo,
                'fecha_pago': datetime.now().isoformat(),
                'estado': 'aprobado',
                'referencia': f"PAG-{pedido_id}-{int(datetime.now().timestamp())}"
            }
            
            logger.info(f"✅ Pago procesado: Pedido #{pedido_id}, ${monto}")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error procesando pago: {str(e)}")
            raise PaymentServiceError(str(e), 500)
    
    @staticmethod
    def enviar_notificacion_whatsapp(pedido_id, monto, cliente_nombre):
        """
        Envía notificación de pago por WhatsApp.
        
        Args:
            pedido_id: ID del pedido
            monto: Monto pagado
            cliente_nombre: Nombre del cliente
            
        Returns:
            Dict con status de envío
        """
        try:
            from urllib.parse import quote
            
            mensaje = (
                f"Hola, quiero pagar el pedido #{pedido_id} "
                f"por un total de ${monto:,.0f} COP. "
                f"Cliente: {cliente_nombre}. Gracias"
            )
            
            wa_link = f"https://wa.me/{PagoService.WHATSAPP_NUMBER}?text={quote(mensaje)}"
            
            logger.info(f"✅ Notificación WhatsApp generada (Pedido #{pedido_id})")
            return {
                'pedido_id': pedido_id,
                'whatsapp_link': wa_link,
                'estado': 'enviado'
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando WhatsApp: {str(e)}")
            raise WhatsAppNotificationError()


# ==================== RUTAS / ENDPOINTS ====================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de health check.
    Usado por Docker y orquestadores para verificar que el servicio está activo.
    """
    return jsonify({
        'status': 'healthy',
        'service': app.config['WHOAMI'],
        'version': app.config['VERSION'],
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/v2/facturas/generar', methods=['POST'])
def generar_factura():
    """
    Genera una factura PDF para un pedido.
    
    Request body:
    {
        "pedido": {
            "id": 123,
            "fecha": "2026-04-16T10:30:00",
            "cliente": {
                "nombre": "John Doe",
                "email": "john@example.com",
                "telefono": "+57 300 123 4567",
                "direccion": "Calle 10 #20-30, Medellín"
            },
            "items": [
                {"nombre": "Silla", "cantidad": 2, "precio": 150000},
                {"nombre": "Mesa", "cantidad": 1, "precio": 450000}
            ],
            "total": 750000
        }
    }
    
    Response: PDF binary
    Status: 200, 400, 500
    """
    try:
        data = request.get_json()
        
        if not data or 'pedido' not in data:
            return error_response("Body debe contener 'pedido'", 400)
        
        pedido = data['pedido']
        pdf_buffer = FacturaService.generar_factura_pdf(pedido)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"factura_pedido_{pedido.get('id', 'desconocido')}.pdf"
        )
        
    except PDFGenerationError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        logger.error(f"❌ Error inesperado en /generar: {str(e)}")
        return error_response("Error interno del servidor", 500)


@app.route('/api/v2/facturas/<int:pedido_id>', methods=['GET'])
def obtener_factura(pedido_id):
    """
    Obtiene una factura previamente generada.
    
    Response: 
    {
        "pedido_id": 123,
        "estado": "disponible",
        "fecha_generacion": "2026-04-16T10:30:00"
    }
    """
    try:
        # Mock: En producción, buscaría en BD o caché
        return jsonify({
            'pedido_id': pedido_id,
            'estado': 'disponible',
            'fecha_generacion': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return error_response(str(e), 500)


@app.route('/api/v2/pagos/procesar', methods=['POST'])
def procesar_pago():
    """
    Procesa un pago.
    
    Request body:
    {
        "pedido_id": 123,
        "monto": 750000,
        "metodo_pago": "Transferencia|Tarjeta|PayPal|MercadoPago"
    }
    
    Response:
    {
        "pedido_id": 123,
        "monto": 750000,
        "metodo": "Transferencia",
        "fecha_pago": "2026-04-16T10:30:00",
        "estado": "aprobado",
        "referencia": "PAG-123-1713274200"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Body no puede estar vacío", 400)
        
        resultado = PagoService.procesar_pago(data)
        return jsonify(resultado), 200
        
    except DatosInvalidosError as e:
        return error_response(e.message, e.status_code)
    except PaymentServiceError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        logger.error(f"❌ Error inesperado en /procesar: {str(e)}")
        return error_response("Error interno del servidor", 500)


@app.route('/api/v2/notificaciones/whatsapp', methods=['POST'])
def enviar_whatsapp():
    """
    Envía notificación de pago por WhatsApp.
    
    Request body:
    {
        "pedido_id": 123,
        "monto": 750000,
        "cliente_nombre": "John Doe"
    }
    
    Response:
    {
        "pedido_id": 123,
        "whatsapp_link": "https://wa.me/573238071236?text=...",
        "estado": "enviado"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Body no puede estar vacío", 400)
        
        resultado = PagoService.enviar_notificacion_whatsapp(
            data.get('pedido_id'),
            data.get('monto'),
            data.get('cliente_nombre', 'Cliente')
        )
        
        return jsonify(resultado), 200
        
    except WhatsAppNotificationError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        logger.error(f"❌ Error inesperado en /whatsapp: {str(e)}")
        return error_response("Error interno del servidor", 500)


@app.route('/api/v2/status', methods=['GET'])
def status():
    """
    Retorna status detallado del microservicio.
    """
    return jsonify({
        'nombre': app.config['WHOAMI'],
        'version': app.config['VERSION'],
        'ambiente': app.config['ENV'],
        'debug': app.config['DEBUG'],
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': '/health',
            'generar_factura': 'POST /api/v2/facturas/generar',
            'obtener_factura': 'GET /api/v2/facturas/<pedido_id>',
            'procesar_pago': 'POST /api/v2/pagos/procesar',
            'notificacion_whatsapp': 'POST /api/v2/notificaciones/whatsapp',
            'status': 'GET /api/v2/status'
        }
    }), 200


# ==================== MANEJADOR DE ERRORES ====================

def error_response(message, status_code):
    """Crea una respuesta de error estructurada"""
    return jsonify({
        'error': True,
        'mensaje': message,
        'timestamp': datetime.now().isoformat(),
        'servicio': app.config['WHOAMI']
    }), status_code


@app.errorhandler(404)
def not_found(error):
    return error_response("Endpoint no encontrado", 404)


@app.errorhandler(500)
def internal_error(error):
    return error_response("Error interno del servidor", 500)


# ==================== MAIN ====================

if __name__ == '__main__':
    logger.info(f"🚀 Iniciando {app.config['WHOAMI']} v{app.config['VERSION']}")
    logger.info(f"   Ambiente: {app.config['ENV']}")
    logger.info(f"   Debug: {app.config['DEBUG']}")
    
    # En desarrollo, usar debug=True; en producción, usar gunicorn
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )
