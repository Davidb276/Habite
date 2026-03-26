"""
Interfaces segregadas para cumplir con Interface Segregation Principle (ISP).

Cada interfaz representa una responsabilidad específica, permitiendo que
los clientes solo dependan de lo que necesitan.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ICartRepository(ABC):
    """Interfaz para lectura del carrito. Solo GET."""
    
    @abstractmethod
    def get(self, cliente_id: int) -> Dict[str, Any]:
        """Obtiene el carrito de un cliente."""
        pass
    
    @abstractmethod
    def get_items(self, cliente_id: int) -> List[Dict[str, Any]]:
        """Obtiene los items del carrito."""
        pass
    
    @abstractmethod
    def get_total(self, cliente_id: int) -> float:
        """Calcula el total del carrito."""
        pass


class ICartModifier(ABC):
    """Interfaz para modificación del carrito. POST, PUT, DELETE."""
    
    @abstractmethod
    def add_item(self, cliente_id: int, producto_id: int, cantidad: int) -> None:
        """Agrega un item al carrito."""
        pass
    
    @abstractmethod
    def remove_item(self, cliente_id: int, producto_id: int) -> None:
        """Remueve un item del carrito."""
        pass
    
    @abstractmethod
    def update_item(self, cliente_id: int, producto_id: int, cantidad: int) -> None:
        """Actualiza la cantidad de un item."""
        pass
    
    @abstractmethod
    def clear(self, cliente_id: int) -> None:
        """Vacía el carrito."""
        pass


class ICheckoutService(ABC):
    """Interfaz para procesar compras. Responsabilidad única."""
    
    @abstractmethod
    def process_purchase(
        self, 
        cliente_id: int, 
        payment_method: str, 
        delivery_address: str,
        usuario=None
    ) -> Dict[str, Any]:
        """Procesa una compra completa.
        
        Retorna información del pedido, pago y envío.
        """
        pass


class IOrderService(ABC):
    """Interfaz para operaciones sobre pedidos."""
    
    @abstractmethod
    def create_order(self, cliente_id: int, productos_data: List, usuario=None) -> Dict:
        """Crea un nuevo pedido."""
        pass
    
    @abstractmethod
    def get_order(self, pedido_id: int) -> Dict:
        """Obtiene un pedido por ID."""
        pass
    
    @abstractmethod
    def update_order_status(self, pedido_id: int, new_status: str) -> None:
        """Actualiza el estado de un pedido."""
        pass


class IPaymentService(ABC):
    """Interfaz para procesar pagos."""
    
    @abstractmethod
    def process_payment(self, pedido_id: int, method: str, amount: float) -> Dict:
        """Procesa el pago de un pedido."""
        pass
    
    @abstractmethod
    def get_payment_methods(self) -> List[str]:
        """Retorna métodos de pago disponibles."""
        pass


class IShippingService(ABC):
    """Interfaz para crear envíos."""
    
    @abstractmethod
    def create_shipment(self, pedido_id: int, address: str) -> Dict:
        """Crea un envío para un pedido."""
        pass


class INotificationService(ABC):
    """Interfaz para notificaciones."""
    
    @abstractmethod
    def send_order_confirmation(self, pedido_id: int, recipient: str) -> None:
        """Envía confirmación de pedido."""
        pass
    
    @abstractmethod
    def send_payment_confirmation(self, pedido_id: int, recipient: str) -> None:
        """Envía confirmación de pago."""
        pass
    
    @abstractmethod
    def send_shipment_notification(self, pedido_id: int, recipient: str, tracking: str = None) -> None:
        """Envía notificación de envío."""
        pass


class IProductRepository(ABC):
    """Interfaz para acceso a datos de productos."""
    
    @abstractmethod
    def get_by_id(self, producto_id: int) -> Dict:
        """Obtiene un producto por ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Dict]:
        """Obtiene todos los productos."""
        pass
    
    @abstractmethod
    def get_by_category(self, categoria: str) -> List[Dict]:
        """Obtiene productos por categoría."""
        pass


class IInventoryService(ABC):
    """Interfaz para gestión de inventario."""
    
    @abstractmethod
    def check_availability(self, producto_id: int, cantidad: int) -> bool:
        """Verifica si hay stock disponible."""
        pass
    
    @abstractmethod
    def reserve_stock(self, producto_id: int, cantidad: int) -> None:
        """Reserva stock para un pedido."""
        pass
    
    @abstractmethod
    def release_stock(self, producto_id: int, cantidad: int) -> None:
        """Libera stock reservado."""
        pass
