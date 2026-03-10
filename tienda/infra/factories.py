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
