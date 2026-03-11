import os
from abc import ABC, abstractmethod


class Notificador(ABC):
    """Interfaz abstracta para notificadores."""
    
    @abstractmethod
    def enviar(self, pedido):
        pass


class EmailNotifierMock(Notificador):
    """Implementación Mock para desarrollo y testing."""
    
    def enviar(self, pedido):
        """Simula el envío de email (solo log en consola)."""
        print(f"[MOCK] EMAIL: Pedido #{pedido.id} creado para {pedido.cliente.nombre}")
        return True


class EmailNotifierReal(Notificador):
    """Implementación real de notificador por email (placeholder)."""
    
    def enviar(self, pedido):
        """Envía email real del pedido (a implementar)."""
        print(f"[PROD] EMAIL: Enviando confirmación de pedido #{pedido.id} a {pedido.cliente.email}")
        # Aquí iría integración con servicio de email real
        # (SendGrid, AWS SES, etc.)
        return True


class NotificadorFactory:
    """
    Factory Pattern para crear instancias de notificadores.
    
    Gestiona la lógica de qué estrategia de notificación usar
    basada en la configuración del ambiente.
    """
    
    @staticmethod
    def crear_notificador() -> Notificador:
        """
        Crea la instancia apropiada de notificador según ENV_TYPE.
        
        Returns:
            Notificador: Instancia del notificador configurado
        """
        env_type = os.getenv("ENV_TYPE", "DEV").upper()
        
        if env_type == "PROD":
            return EmailNotifierReal()
        else:
            # Por defecto usa Mock en desarrollo
            return EmailNotifierMock()


# ===================== PASARELAS DE PAGO =====================

class Pasarela(ABC):
    """Interfaz abstracta para pasarelas de pago."""
    
    @abstractmethod
    def procesar(self, monto, metodo):
        """
        Procesa el pago en la pasarela.
        
        Args:
            monto: Monto a procesar
            metodo: Método de pago (tarjeta, transferencia, etc.)
        
        Returns:
            dict con resultado del pago {
                'exito': bool,
                'id_transaccion': str,
                'mensaje': str
            }
        
        Raises:
            ValidationError: Si hay error en el procesamiento
        """
        pass


class PasarelaMock(Pasarela):
    """Implementación Mock para desarrollo y testing."""
    
    def procesar(self, monto, metodo):
        """Simula el procesamiento de pago (siempre exitoso)."""
        print(f"[MOCK] PAGO: Procesando ${monto} con {metodo}")
        return {
            'exito': True,
            'id_transaccion': f'MOCK_{int(monto*100)}',
            'mensaje': 'Pago simulado exitosamente'
        }


class PasarelaStripe(Pasarela):
    """Implementación de Stripe para pagos."""
    
    def procesar(self, monto, metodo):
        """Procesa pago a través de Stripe API."""
        print(f"[STRIPE] PAGO: Procesando ${monto} con {metodo}")
        # Aquí iría integración real con Stripe
        # import stripe
        # stripe.api_key = settings.STRIPE_SECRET_KEY
        # charge = stripe.Charge.create(...)
        return {
            'exito': True,
            'id_transaccion': f'ch_stripe_{int(monto*100)}',
            'mensaje': 'Pago procesado por Stripe'
        }


class PasarelaMercadoPago(Pasarela):
    """Implementación de MercadoPago para pagos."""
    
    def procesar(self, monto, metodo):
        """Procesa pago a través de MercadoPago API."""
        print(f"[MERCADOPAGO] PAGO: Procesando ${monto} con {metodo}")
        # Aquí iría integración real con MercadoPago
        # from mercadopago import preferences
        # pref = preferences.Preference(...)
        return {
            'exito': True,
            'id_transaccion': f'mp_payment_{int(monto*100)}',
            'mensaje': 'Pago procesado por MercadoPago'
        }


class PasarelaPayPal(Pasarela):
    """Implementación de PayPal para pagos."""
    
    def procesar(self, monto, metodo):
        """Procesa pago a través de PayPal API."""
        print(f"[PAYPAL] PAGO: Procesando ${monto} con {metodo}")
        # Aquí iría integración real con PayPal
        # from paypalrestsdk import Payment
        # payment = Payment({...})
        return {
            'exito': True,
            'id_transaccion': f'pp_payment_{int(monto*100)}',
            'mensaje': 'Pago procesado por PayPal'
        }


class PasarelaFactory:
    """
    Factory Pattern para pasarelas de pago.
    
    Permite cambiar entre diferentes proveedores sin modificar
    el código de negocio (cumple DIP y Open/Closed).
    """
    
    @staticmethod
    def crear_pasarela(proveedor=None) -> Pasarela:
        """
        Crea la instancia apropiada de pasarela según configuración.
        
        Args:
            proveedor: Nombre del proveedor ('stripe', 'mercadopago', 'paypal')
                      Si es None, usa ENV_PAYMENT_PROVIDER
        
        Returns:
            Pasarela: Instancia de la pasarela configurada
        """
        if proveedor is None:
            proveedor = os.getenv("ENV_PAYMENT_PROVIDER", "MOCK").upper()
        else:
            proveedor = proveedor.upper()
        
        proveedores = {
            'STRIPE': PasarelaStripe,
            'MERCADOPAGO': PasarelaMercadoPago,
            'PAYPAL': PasarelaPayPal,
            'MOCK': PasarelaMock,
        }
        
        clase_pasarela = proveedores.get(proveedor, PasarelaMock)
        return clase_pasarela()
