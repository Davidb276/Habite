"""
Estrategias de pago para cumplir con Open/Closed Principle.

Cada método de pago tiene su propia estrategia, permitiendo
extensión sin modificación del código existente.
"""

from abc import ABC, abstractmethod


class PaymentMethodStrategy(ABC):
    """Interfaz para estrategias de método de pago."""
    
    @abstractmethod
    def get_payment_status(self) -> str:
        """Retorna el estado del pago después de procesarlo."""
        pass
    
    @abstractmethod
    def get_order_status(self) -> str:
        """Retorna el estado del pedido después de procesarlo."""
        pass
    
    @abstractmethod
    def requires_immediate_confirmation(self) -> bool:
        """Indica si el pago requiere confirmación inmediata."""
        pass


class AdvancePaymentStrategy(PaymentMethodStrategy):
    """Estrategia para pagos adelantados (tarjeta, PayPal, etc.)."""
    
    def get_payment_status(self) -> str:
        """El pago se marca como Pagado inmediatamente."""
        return "Pagado"
    
    def get_order_status(self) -> str:
        """El pedido se marca como Pagado."""
        return "Pagado"
    
    def requires_immediate_confirmation(self) -> bool:
        """Requiere confirmación inmediata."""
        return True


class CashOnDeliveryStrategy(PaymentMethodStrategy):
    """Estrategia para pagos contra entrega."""
    
    def get_payment_status(self) -> str:
        """El pago se marca como Pendiente."""
        return "Pendiente"
    
    def get_order_status(self) -> str:
        """El pedido se marca como Pendiente."""
        return "Pendiente"
    
    def requires_immediate_confirmation(self) -> bool:
        """No requiere confirmación inmediata."""
        return False


class DepositPaymentStrategy(PaymentMethodStrategy):
    """Estrategia para pagos con depósito (50% adelante, 50% en entrega)."""
    
    def get_payment_status(self) -> str:
        """Pago parcial confirmado."""
        return "Parcialmente Pagado"
    
    def get_order_status(self) -> str:
        """Pedido en espera de pago restante."""
        return "Parcialmente Pagado"
    
    def requires_immediate_confirmation(self) -> bool:
        """Requiere confirmación del depósito."""
        return True


class PaymentStrategyFactory:
    """Factory para crear estrategias de pago.
    
    Implementa el patrón Factory permitiendo fácil extensión
    sin modificar el código de checkout.
    """
    
    _strategies = {
        "Pago Adelantado": AdvancePaymentStrategy,
        "Contra Entrega": CashOnDeliveryStrategy,
        "Depósito": DepositPaymentStrategy,
        "Tarjeta de Crédito": AdvancePaymentStrategy,
        "PayPal": AdvancePaymentStrategy,
        "Mercado Pago": AdvancePaymentStrategy,
    }
    
    @classmethod
    def register_strategy(cls, method: str, strategy_class: type) -> None:
        """Registra una nueva estrategia de pago dinámicamente.
        
        Permite extensión sin tocar el código existente (OCP).
        """
        if not issubclass(strategy_class, PaymentMethodStrategy):
            raise TypeError(f"{strategy_class} debe heredar de PaymentMethodStrategy")
        cls._strategies[method] = strategy_class
    
    @classmethod
    def get_strategy(cls, method: str) -> PaymentMethodStrategy:
        """Obtiene la estrategia para un método de pago.
        
        Args:
            method: Nombre del método de pago
            
        Returns:
            Instancia de la estrategia correspondiente
            
        Raises:
            ValueError: Si el método no está registrado
        """
        if method not in cls._strategies:
            raise ValueError(
                f"Método de pago '{method}' no reconocido. "
                f"Métodos disponibles: {', '.join(cls._strategies.keys())}"
            )
        return cls._strategies[method]()
    
    @classmethod
    def get_available_methods(cls) -> list:
        """Retorna lista de métodos de pago disponibles."""
        return list(cls._strategies.keys())
