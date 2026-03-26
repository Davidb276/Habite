"""
Excepciones personalizadas para el dominio.

Permite manejo de errores consistente y específico,
cumpliendo con el principio de Least Surprise.
"""


class HabiteException(Exception):
    """Excepción base para todas las excepciones del dominio."""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# ======================== ERRORES DE CARRITO ========================

class CartException(HabiteException):
    """Excepción base para errores del carrito."""
    pass


class CartNotFound(CartException):
    """El carrito no existe."""
    
    def __init__(self, cliente_id: int):
        super().__init__(
            f"No se encontró carrito para el cliente {cliente_id}",
            code="CART_NOT_FOUND"
        )


class CartItemNotFound(CartException):
    """El item no existe en el carrito."""
    
    def __init__(self, producto_id: int):
        super().__init__(
            f"El producto {producto_id} no está en el carrito",
            code="CART_ITEM_NOT_FOUND"
        )


class InvalidCartQuantity(CartException):
    """La cantidad del carrito es inválida."""
    
    def __init__(self, cantidad: int):
        super().__init__(
            f"La cantidad {cantidad} es inválida. Debe ser mayor a 0",
            code="INVALID_CART_QUANTITY"
        )


# ======================== ERRORES DE PEDIDO ========================

class OrderException(HabiteException):
    """Excepción base para errores de pedidos."""
    pass


class OrderNotFound(OrderException):
    """El pedido no existe."""
    
    def __init__(self, pedido_id: int):
        super().__init__(
            f"No se encontró el pedido {pedido_id}",
            code="ORDER_NOT_FOUND"
        )


class EmptyCart(OrderException):
    """Se intenta crear un pedido con carrito vacío."""
    
    def __init__(self):
        super().__init__(
            "No se puede crear un pedido con carrito vacío",
            code="EMPTY_CART"
        )


class InvalidOrderStatus(OrderException):
    """El estado del pedido es inválido."""
    
    def __init__(self, status: str):
        super().__init__(
            f"El estado '{status}' no es válido",
            code="INVALID_ORDER_STATUS"
        )


# ======================== ERRORES DE PAGO ========================

class PaymentException(HabiteException):
    """Excepción base para errores de pago."""
    pass


class PaymentProcessingError(PaymentException):
    """Error al procesar el pago."""
    
    def __init__(self, message: str, reason: str = None):
        super().__init__(
            message,
            code="PAYMENT_PROCESSING_ERROR"
        )
        self.reason = reason


class InvalidPaymentMethod(PaymentException):
    """Método de pago no válido."""
    
    def __init__(self, method: str):
        super().__init__(
            f"El método de pago '{method}' no es válido",
            code="INVALID_PAYMENT_METHOD"
        )


class PaymentAmountMismatch(PaymentException):
    """Monto de pago no coincide con el total del pedido."""
    
    def __init__(self, expected: float, received: float):
        super().__init__(
            f"Monto incorrecto. Esperado: {expected}, Recibido: {received}",
            code="PAYMENT_AMOUNT_MISMATCH"
        )


# ======================== ERRORES DE STOCK ========================

class InventoryException(HabiteException):
    """Excepción base para errores de inventario."""
    pass


class InsufficientStock(InventoryException):
    """Stock insuficiente para el producto."""
    
    def __init__(self, producto_id: int, requested: int, available: int):
        super().__init__(
            f"Stock insuficiente para producto {producto_id}. "
            f"Solicitado: {requested}, Disponible: {available}",
            code="INSUFFICIENT_STOCK"
        )


class ProductNotFound(InventoryException):
    """El producto no existe."""
    
    def __init__(self, producto_id: int):
        super().__init__(
            f"No se encontró el producto {producto_id}",
            code="PRODUCT_NOT_FOUND"
        )


# ======================== ERRORES DE CLIENTE ========================

class ClientException(HabiteException):
    """Excepción base para errores de cliente."""
    pass


class ClientNotFound(ClientException):
    """El cliente no existe."""
    
    def __init__(self, cliente_id: int):
        super().__init__(
            f"No se encontró el cliente {cliente_id}",
            code="CLIENT_NOT_FOUND"
        )


class InvalidClientData(ClientException):
    """Datos de cliente inválidos."""
    
    def __init__(self, message: str):
        super().__init__(message, code="INVALID_CLIENT_DATA")


# ======================== ERRORES DE ENVÍO ========================

class ShippingException(HabiteException):
    """Excepción base para errores de envío."""
    pass


class InvalidShippingAddress(ShippingException):
    """Dirección de envío inválida."""
    
    def __init__(self, address: str):
        super().__init__(
            f"Dirección de envío inválida: {address}",
            code="INVALID_SHIPPING_ADDRESS"
        )
