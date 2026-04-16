from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta
from tienda.domain.builders import PedidoBuilder
from tienda.infra.factories import NotificadorFactory, PasarelaFactory
from tienda.models import Cliente, Producto, Pedido, Inventario, Pago, Envio, Carrito, CarritoItem
from django.core.exceptions import ValidationError


class InventarioService:
    """Gestiona la lógica de negocio para inventario."""
    
    @staticmethod
    def verificar_disponibilidad(producto_id, cantidad):
        """Valida si hay stock disponible del producto."""
        try:
            inventario = Inventario.objects.get(producto_id=producto_id)
            return inventario.cantidad_disponible >= cantidad
        except Inventario.DoesNotExist:
            return False
    
    @staticmethod
    def reducir_stock(producto_id, cantidad):
        """Reduce el stock del producto. Lanza excepción si no hay suficiente."""
        try:
            inventario = Inventario.objects.get(producto_id=producto_id)
            if inventario.cantidad_disponible < cantidad:
                raise ValidationError(
                    f"Stock insuficiente. Disponible: {inventario.cantidad_disponible}"
                )
            inventario.cantidad_disponible -= cantidad
            inventario.save()
            return True
        except Inventario.DoesNotExist:
            raise ValidationError("Inventario no encontrado para este producto")


class PedidoService:
    """dirige la lógica de creación y gestión de pedidos."""
    
    def __init__(self):
        self.notificador = NotificadorFactory.crear_notificador()
    
    @transaction.atomic
    def crear_pedido(self, cliente_id, productos_data, usuario=None):
        """
        Crea un pedido con validación de stock y cálculo de total.
        
        Args:
            cliente_id: ID del cliente
            productos_data: Lista de tuplas (producto_id, cantidad)
        
        Returns:
            Pedido creado
        
        Raises:
            ValidationError: Si hay validaciones que fallan
        """
        # Validar cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            raise ValidationError("Cliente no encontrado")
        
        # Validar y reservar stock
        for prod_id, cantidad in productos_data:
            try:
                Producto.objects.get(id=prod_id)
            except Producto.DoesNotExist:
                raise ValidationError(f"Producto {prod_id} no encontrado")
            
            if not InventarioService.verificar_disponibilidad(prod_id, cantidad):
                raise ValidationError(f"Stock insuficiente para producto {prod_id}")
        
        # Construir pedido usando Builder
        builder = PedidoBuilder().para_cliente(cliente)
        
        for prod_id, cantidad in productos_data:
            producto = Producto.objects.get(id=prod_id)
            builder.agregar_item(producto, cantidad)
            # Reducir stock después de validar
            InventarioService.reducir_stock(prod_id, cantidad)
        
        pedido = builder.build()
        if usuario:
            pedido.usuario = usuario
            pedido.save(update_fields=["usuario"])
        
        # Calcular y establecer total
        self._calcular_total_pedido(pedido)
        
        # Notificar
        self.notificador.enviar(pedido)
        
        return pedido
    
    @staticmethod
    def _calcular_total_pedido(pedido):
        """Calcula el total del pedido basado en sus items."""
        total = sum(item.producto.precio * item.cantidad for item in pedido.items.all())
        pedido.total = total
        pedido.save()
        return total
    
    @staticmethod
    def actualizar_estado_pedido(pedido_id, nuevo_estado):
        """Actualiza el estado del pedido."""
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            pedido.estado = nuevo_estado
            pedido.save()
            return pedido
        except Pedido.DoesNotExist:
            raise ValidationError("Pedido no encontrado")


class PagoService:
    """Gestiona la lógica de procesamiento de pagos."""
    
    def __init__(self, pasarela=None):
        """
        Inyección de dependencias para cumplir DIP.
        
        Args:
            pasarela: Instancia de pasarela de pago (default: PasarelaFactory)
        """
        self.pasarela = pasarela or PasarelaFactory.crear_pasarela()
    
    def procesear_pago(self, pedido_id, metodo_pago, monto):
        """
        Procesa el pago de un pedido usando la pasarela inyectada.
        Utiliza estrategias de pago para cumplir con OCP.
        
        Args:
            pedido_id: ID del pedido
            metodo_pago: Método de pago (Tarjeta de Crédito, PayPal, Pago Adelantado, Contra Entrega, etc.)
            monto: Monto a procesar
        
        Returns:
            Pago: Registro de pago creado
        
        Raises:
            ValidationError: Si el pedido no existe o hay conflicto
        """
        from tienda.domain.strategies import PaymentStrategyFactory
        
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            raise ValidationError("Pedido no encontrado")
        
        # Validar que el monto coincida
        if monto != pedido.total:
            raise ValidationError(f"Monto incorrecto. Total esperado: {pedido.total}")
        
        # Delegar procesamiento a la pasarela
        resultado_pago = self.pasarela.procesar(monto, metodo_pago)
        
        if not resultado_pago.get('exito'):
            raise ValidationError(f"Error en pasarela: {resultado_pago.get('mensaje', 'Error desconocido')}")
        
        # Obtener estrategia de pago - Cumple con OCP
        try:
            estrategia_pago = PaymentStrategyFactory.get_strategy(metodo_pago)
        except ValueError as e:
            # Si no existe estrategia, usar comportamiento por defecto (Pendiente)
            estrategia_pago = PaymentStrategyFactory.get_strategy("Contra Entrega")
        
        # Obtener estados desde la estrategia (sin if/elif hardcodeado)
        estado_pago = estrategia_pago.get_payment_status()
        estado_pedido = estrategia_pago.get_order_status()
        
        # Crear registro de pago en BD
        pago = Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo_pago,
            monto=monto,
            estado=estado_pago
        )
        
        # Actualizar estado del pedido
        pedido.estado = estado_pedido
        pedido.save()
        
        return pago
    
    @staticmethod
    def obtener_pago_pedido(pedido_id):
        """Obtiene el registro de pago de un pedido."""
        try:
            return Pago.objects.get(pedido_id=pedido_id)
        except Pago.DoesNotExist:
            return None


class EnvioService:
    """Gestiona la lógica de envíos."""
    
    @staticmethod
    def crear_envio(pedido_id, direccion_entrega):
        """Crea un registro de envío para un pedido."""
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            raise ValidationError("Pedido no encontrado")
        
        envio = Envio.objects.create(
            pedido=pedido,
            direccion_entrega=direccion_entrega,
            estado_envio="Preparando"
        )
        return envio
    
    @staticmethod
    def actualizar_estado_envio(envio_id, nuevo_estado):
        """Actualiza el estado del envío."""
        try:
            envio = Envio.objects.get(id=envio_id)
            envio.estado_envio = nuevo_estado
            envio.save()
            return envio
        except Envio.DoesNotExist:
            raise ValidationError("Envío no encontrado")


class CartService:
    """Gestiona la lógica del carrito de compras."""
    
    def __init__(self, pedido_service=None, pago_service=None, envio_service=None):
        """
        Inyección de dependencias para cumplir DIP (Dependency Inversion Principle).
        
        Args:
            pedido_service: Servicio de pedidos (default: PedidoService)
            pago_service: Servicio de pagos (default: PagoService)
            envio_service: Servicio de envíos (default: EnvioService)
        """
        self.pedido_service = pedido_service or PedidoService()
        self.pago_service = pago_service or PagoService()
        self.envio_service = envio_service or EnvioService()
    
    @staticmethod
    def obtener_o_crear_carrito(cliente_id):
        """Obtiene o crea el carrito para un cliente."""
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            raise ValidationError("Cliente no encontrado")
        
        carrito, created = Carrito.objects.get_or_create(cliente=cliente)
        return carrito
    
    @staticmethod
    def agregar_item(cliente_id, producto_id, cantidad):
        """Agrega un producto al carrito o actualiza su cantidad."""
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            producto = Producto.objects.get(id=producto_id)
        except Cliente.DoesNotExist:
            raise ValidationError("Cliente no encontrado")
        except Producto.DoesNotExist:
            raise ValidationError("Producto no encontrado")
        
        if cantidad <= 0:
            raise ValidationError("Cantidad debe ser mayor a 0")
        
        # Verificar disponibilidad
        if not InventarioService.verificar_disponibilidad(producto_id, cantidad):
            raise ValidationError(f"Stock insuficiente para {producto.nombre}")
        
        carrito = CartService.obtener_o_crear_carrito(cliente_id)
        
        item, created = CarritoItem.objects.update_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': cantidad}
        )
        return item
    
    @staticmethod
    def eliminar_item(cliente_id, producto_id):
        """Elimina un producto del carrito."""
        try:
            carrito = CartService.obtener_o_crear_carrito(cliente_id)
            CarritoItem.objects.filter(carrito=carrito, producto_id=producto_id).delete()
            return True
        except ValidationError:
            raise
    
    @staticmethod
    def vaciar_carrito(cliente_id):
        """Vacía todo el carrito del cliente."""
        try:
            carrito = CartService.obtener_o_crear_carrito(cliente_id)
            CarritoItem.objects.filter(carrito=carrito).delete()
            return True
        except ValidationError:
            raise
    
    @staticmethod
    def obtener_carrito(cliente_id):
        """Obtiene el carrito con todos sus items."""
        carrito = CartService.obtener_o_crear_carrito(cliente_id)
        return carrito
    
    @staticmethod
    def calcular_total_carrito(cliente_id):
        """Calcula el total del carrito."""
        carrito = CartService.obtener_o_crear_carrito(cliente_id)
        total = sum(
            item.producto.precio * item.cantidad 
            for item in carrito.items.all()
        )
        return float(total)
    
    @transaction.atomic
    def crear_pedido_desde_carrito(self, cliente_id, metodo_pago, direccion_entrega, usuario=None):
        """
        Crea un pedido a partir del carrito y procesa pago y envío.
        Reutiliza pedidos pendientes SOLO si tienen los MISMOS items del carrito.
        Si cambian los items, crea un nuevo pedido.
        Aplica descuento para "Pago Adelantado".
        
        Args:
            cliente_id: ID del cliente
            metodo_pago: Método de pago
            direccion_entrega: Dirección para el envío
        
        Returns:
            dict con pedido, pago y envío
        """
        carrito = self.obtener_carrito(cliente_id)
        
        if not carrito.items.exists():
            raise ValidationError("El carrito está vacío")
        
        # Obtener items del carrito actual
        items_carrito_set = set(
            (item.producto_id, item.cantidad)
            for item in carrito.items.all()
        )
        
        # Verificar si existe un pedido pendiente del cliente
        try:
            pedido_pendiente = Pedido.objects.filter(
                cliente_id=cliente_id,
                estado="Pendiente"
            ).latest('fecha')
            
            # Obtener items del pedido pendiente
            items_pedido_set = set(
                (item.producto_id, item.cantidad)
                for item in pedido_pendiente.items.all()
            )
            
            # Si los items son iguales, reutilizar
            if items_carrito_set == items_pedido_set:
                pago = Pago.objects.get(pedido_id=pedido_pendiente.id)
                pago.metodo_pago = metodo_pago
                pago.monto = pedido_pendiente.total
                pago.save()
                
                envio = Envio.objects.get(pedido_id=pedido_pendiente.id)
                envio.direccion_entrega = direccion_entrega
                envio.save()
                
                return {
                    "pedido": pedido_pendiente,
                    "pago": pago,
                    "envio": envio
                }
        except Pedido.DoesNotExist:
            pass
        
        # Si no existe pedido pendiente o los items cambiaron, crear uno nuevo
        productos_data = list(items_carrito_set)
        
        # Delegar a servicios inyectados (cumple DIP)
        pedido = self.pedido_service.crear_pedido(cliente_id, productos_data, usuario=usuario)
        
        # Aplicar descuento o recargo según método de pago
        DESCUENTO_PAGO_ADELANTADO = Decimal('0.03')  # 3% descuento
        if metodo_pago == "Pago Adelantado":
            descuento = pedido.total * DESCUENTO_PAGO_ADELANTADO
            pedido.total -= descuento
            pedido.save()
        
        pago = self.pago_service.procesear_pago(pedido.id, metodo_pago, pedido.total)
        envio = self.envio_service.crear_envio(pedido.id, direccion_entrega)
        
        # NO vaciar carrito aquí - dejarlo para cuando el pago se confirme
        # self.vaciar_carrito(cliente_id)
        
        return {
            "pedido": pedido,
            "pago": pago,
            "envio": envio
        }


class FacturaService:
    """Gestiona la generación de facturas en PDF."""
    
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from datetime import datetime
    from io import BytesIO
    
    @staticmethod
    def generar_factura_pdf(pedido):
        """
        Genera una factura en PDF para un pedido.
        
        Args:
            pedido: Instancia del modelo Pedido
            
        Returns:
            BytesIO con el contenido del PDF
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib import colors
        from io import BytesIO
        
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
            ['Número de Pedido:', f'#{pedido.id}'],
            ['Fecha:', pedido.fecha.strftime('%d/%m/%Y %H:%M')],
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
        elements.append(Paragraph("<b>Datos de Envío</b>", heading_style))
        elements.append(Paragraph(f"<b>Cliente:</b> {pedido.cliente.nombre}", styles['Normal']))
        elements.append(Paragraph(f"<b>Email:</b> {pedido.cliente.email}", styles['Normal']))
        elements.append(Paragraph(f"<b>Teléfono:</b> {pedido.cliente.telefono}", styles['Normal']))
        elements.append(Paragraph(f"<b>Dirección:</b> {pedido.cliente.direccion}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Items del pedido
        elements.append(Paragraph("<b>Detalles del Pedido</b>", heading_style))
        
        items_data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
        total_items = 0
        
        for item in pedido.items.all():
            subtotal = float(item.producto.precio) * item.cantidad
            total_items += subtotal
            items_data.append([
                item.producto.nombre,
                str(item.cantidad),
                f"${item.producto.precio:,.2f}",
                f"${subtotal:,.2f}"
            ])
        
        items_data.append(['', '', 'TOTAL:', f"${total_items:,.2f}"])
        
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
        return pdf_buffer
