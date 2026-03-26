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
    """Factory Pattern para pasarelas de pago.
    
    Implementa registro dinámico de pasarelas para cumplir con OCP.
    Nuevas pasarelas pueden agregarse sin modificar este código.
    """
    
    _pasarelas = {
        'STRIPE': PasarelaStripe,
        'MERCADOPAGO': PasarelaMercadoPago,
        'PAYPAL': PasarelaPayPal,
        'MOCK': PasarelaMock,
    }
    
    @classmethod
    def register_pasarela(cls, nombre: str, clase_pasarela: type) -> None:
        """Registra una nueva pasarela dinámicamente.
        
        Permite extensión sin modificar el código (OCP).
        
        Args:
            nombre: Nombre identificador de la pasarela
            clase_pasarela: Clase que implementa Pasarela
            
        Raises:
            TypeError: Si la clase no hereda de Pasarela
        """
        if not issubclass(clase_pasarela, Pasarela):
            raise TypeError(f"{clase_pasarela} debe heredar de Pasarela")
        cls._pasarelas[nombre.upper()] = clase_pasarela
    
    @classmethod
    def crear_pasarela(cls, proveedor=None) -> Pasarela:
        """Crea una instancia de pasarela.
        
        Args:
            proveedor: Nombre del proveedor. Si es None, usa variable de entorno.
                      Soporta: STRIPE, MERCADOPAGO, PAYPAL, MOCK
        
        Returns:
            Pasarela: Instancia de la pasarela
        """
        if proveedor is None:
            proveedor = os.getenv("ENV_PAYMENT_PROVIDER", "MOCK").upper()
        else:
            proveedor = proveedor.upper()
        
        clase_pasarela = cls._pasarelas.get(proveedor, PasarelaMock)
        return clase_pasarela()
    
    @classmethod
    def get_disponibles(cls) -> list:
        """Retorna lista de pasarelas disponibles."""
        return list(cls._pasarelas.keys())
