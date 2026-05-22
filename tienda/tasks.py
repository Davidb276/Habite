from __future__ import annotations

from datetime import date
from decimal import Decimal

import requests
from celery import shared_task
from django.conf import settings

from .models import Pedido


@shared_task
def enviar_notificacion_compra_async(pedido_id: int, email: str, total: float, metodo_pago: str) -> dict:
    """Envía una notificación de compra en segundo plano."""
    payload = {
        'pedido_id': pedido_id,
        'cliente_email': email,
        'total': float(total),
        'metodo_pago': metodo_pago,
    }

    try:
        response = requests.post(
            f"{settings.HABITE_PAYMENT_SERVICE_URL}/api/v2/notificaciones/whatsapp",
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return {'ok': True, 'pedido_id': pedido_id, 'response': response.json()}
    except Exception as exc:
        return {'ok': False, 'pedido_id': pedido_id, 'error': str(exc)}


@shared_task
def generar_reporte_ventas_async(fecha_str: str | None = None) -> dict:
    """Genera un resumen diario de ventas."""
    fecha_reporte = date.fromisoformat(fecha_str) if fecha_str else date.today()
    pedidos = Pedido.objects.filter(fecha__date=fecha_reporte)
    total_ventas = sum(Decimal(str(pedido.total)) for pedido in pedidos)

    return {
        'fecha': fecha_reporte.isoformat(),
        'cantidad_pedidos': pedidos.count(),
        'total_ventas': float(total_ventas),
        'pedido_ids': list(pedidos.values_list('id', flat=True)),
    }