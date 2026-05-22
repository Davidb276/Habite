"""Microservicio Flask para catálogo, inventario, carrito y pedidos.

Usa el ORM de Django sobre la misma base de datos durante la transición para
que el monolito pueda delegar la lógica sin perder consistencia.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Iterable

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DJANGO_PROJECT_ROOT = os.getenv("DJANGO_PROJECT_ROOT", "/workspace")
if DJANGO_PROJECT_ROOT not in sys.path:
    sys.path.insert(0, DJANGO_PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "habite_project.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402
from django.db import transaction  # noqa: E402

from tienda.models import Carrito, CarritoItem, Categoria, Cliente, Envio, Inventario, Pedido, PedidoItem, Producto  # noqa: E402
from integrations.adapters import JsonPlaceholderAdapter  # noqa: E402


app = Flask(__name__)
CORS(app)


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"
    WHOAMI = os.getenv("MICROSERVICE_NAME", "Habite Core Service")
    VERSION = "1.0.0"
    PAYMENT_SERVICE_URL = os.getenv("HABITE_PAYMENT_SERVICE_URL", "http://flask_payment:5000").rstrip("/")


app.config.from_object(Config)


def error_response(message: str, status_code: int):
    return jsonify({
        "error": True,
        "mensaje": message,
        "timestamp": datetime.now().isoformat(),
        "servicio": app.config["WHOAMI"],
    }), status_code


def serialize_producto(producto: Producto) -> Dict[str, Any]:
    return {
        "id": producto.id,
        "nombre": producto.nombre,
        "precio": float(producto.precio),
        "categoria": producto.categoria,
        "descripcion": producto.descripcion,
        "imagen": producto.imagen.url if producto.imagen else None,
        "es_premium": producto.es_premium,
        "en_oferta": producto.en_oferta,
        "descuento_porcentaje": float(producto.descuento_porcentaje),
        "precio_descuento": float(producto.get_precio_descuento()),
        "descuento_monetario": float(producto.get_descuento_monetario()),
    }


def serialize_categoria(categoria: Categoria) -> Dict[str, Any]:
    return {
        "id": categoria.id,
        "nombre": categoria.nombre,
        "slug": categoria.slug,
        "descripcion": categoria.descripcion,
        "imagen": categoria.imagen.url if categoria.imagen else None,
        "icono": categoria.icono,
        "orden": categoria.orden,
    }


def serialize_cliente(cliente: Cliente) -> Dict[str, Any]:
    return {
        "id": cliente.id,
        "nombre": cliente.nombre,
        "email": cliente.email,
        "direccion": cliente.direccion,
        "telefono": cliente.telefono,
    }


def serialize_pedido_item(item: PedidoItem) -> Dict[str, Any]:
    return {
        "id": item.id,
        "producto_id": item.producto_id,
        "producto_nombre": item.producto.nombre,
        "precio_unitario": float(item.producto.precio),
        "cantidad": item.cantidad,
        "subtotal": float(item.get_subtotal()),
    }


def serialize_pedido(pedido: Pedido) -> Dict[str, Any]:
    return {
        "id": pedido.id,
        "cliente": serialize_cliente(pedido.cliente),
        "usuario_id": pedido.usuario_id,
        "usuario_username": pedido.usuario.username if pedido.usuario else None,
        "usuario_email": pedido.usuario.email if pedido.usuario else None,
        "total": float(pedido.total),
        "estado": pedido.estado,
        "fecha": pedido.fecha.isoformat() if pedido.fecha else None,
        "items": [serialize_pedido_item(item) for item in pedido.items.select_related("producto").all()],
    }


def serialize_envio(envio: Envio) -> Dict[str, Any]:
    return {
        "id": envio.id,
        "pedido_id": envio.pedido_id,
        "direccion_entrega": envio.direccion_entrega,
        "estado_envio": envio.estado_envio,
    }


def serialize_carrito_item(item: CarritoItem) -> Dict[str, Any]:
    return {
        "id": item.id,
        "producto_id": item.producto_id,
        "producto_nombre": item.producto.nombre,
        "precio_unitario": float(item.producto.precio),
        "cantidad": item.cantidad,
        "subtotal": float(item.producto.precio * item.cantidad),
    }


def serialize_carrito(carrito: Carrito) -> Dict[str, Any]:
    items = list(carrito.items.select_related("producto").all())
    return {
        "id": carrito.id,
        "cliente_id": carrito.cliente_id,
        "items": [serialize_carrito_item(item) for item in items],
        "total": float(sum(item.producto.precio * item.cantidad for item in items)),
        "cantidad_items": len(items),
        "fecha_creacion": carrito.fecha_creacion.isoformat() if carrito.fecha_creacion else None,
    }


def obtener_o_crear_carrito(cliente: Cliente) -> Carrito:
    carrito, _ = Carrito.objects.get_or_create(cliente=cliente)
    return carrito


def obtener_usuario(payload: Dict[str, Any] | None) -> User | None:
    if not payload:
        return None
    if payload.get("id"):
        try:
            return User.objects.get(id=payload["id"])
        except User.DoesNotExist:
            return None
    if payload.get("email"):
        return User.objects.filter(email=payload["email"]).first()
    return None


def obtener_cliente_por_payload(payload: Dict[str, Any]) -> Cliente:
    email = payload.get("email")
    if not email:
        raise ValidationError("email es requerido")
    cliente, _ = Cliente.objects.get_or_create(
        email=email,
        defaults={
            "nombre": payload.get("nombre") or email,
            "direccion": payload.get("direccion") or "Por definir",
            "telefono": payload.get("telefono") or "Por definir",
        },
    )
    if payload.get("nombre"):
        cliente.nombre = payload["nombre"]
    if payload.get("direccion"):
        cliente.direccion = payload["direccion"]
    if payload.get("telefono"):
        cliente.telefono = payload["telefono"]
    cliente.save()
    return cliente


def validar_inventario(producto_id: int, cantidad: int) -> Inventario:
    inventario = Inventario.objects.select_related("producto").get(producto_id=producto_id)
    if inventario.cantidad_disponible < cantidad:
        raise ValidationError(f"Stock insuficiente. Disponible: {inventario.cantidad_disponible}")
    return inventario


def reducir_stock(producto_id: int, cantidad: int) -> Dict[str, Any]:
    inventario = validar_inventario(producto_id, cantidad)
    inventario.cantidad_disponible -= cantidad
    inventario.save(update_fields=["cantidad_disponible"])
    return {
        "exito": True,
        "producto_id": producto_id,
        "cantidad_reducida": cantidad,
        "cantidad_disponible": inventario.cantidad_disponible,
    }


def crear_pedido_interno(cliente_id: int, productos: Iterable[Dict[str, Any]], usuario: User | None = None) -> Pedido:
    cliente = Cliente.objects.get(id=cliente_id)

    with transaction.atomic():
        pedido = Pedido.objects.create(cliente=cliente, usuario=usuario)
        total = Decimal("0")

        for item in productos:
            producto = Producto.objects.get(id=item["producto_id"])
            cantidad = int(item["cantidad"])
            validar_inventario(producto.id, cantidad)
            PedidoItem.objects.create(pedido=pedido, producto=producto, cantidad=cantidad)
            reducir_stock(producto.id, cantidad)
            total += producto.precio * cantidad

        pedido.total = total
        pedido.save(update_fields=["total"])
        return pedido


def pagar_y_crear_envio(pedido: Pedido, metodo_pago: str, direccion_entrega: str) -> Dict[str, Any]:
    import requests

    pago_response = requests.post(
        f"{app.config['PAYMENT_SERVICE_URL']}/api/v2/pagos/procesar",
        json={
            "pedido_id": pedido.id,
            "monto": float(pedido.total),
            "metodo_pago": metodo_pago,
        },
        timeout=20,
    )
    pago_response.raise_for_status()
    pago_data = pago_response.json()

    envio = Envio.objects.create(
        pedido=pedido,
        direccion_entrega=direccion_entrega,
        estado_envio="Preparando",
    )

    if pago_data.get("estado") == "aprobado":
        pedido.estado = "Pagado"
        pedido.save(update_fields=["estado"])

    return {
        "pedido": serialize_pedido(pedido),
        "pago": pago_data,
        "envio": serialize_envio(envio),
    }


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": app.config["WHOAMI"],
        "version": app.config["VERSION"],
        "timestamp": datetime.now().isoformat(),
    }), 200


@app.route("/api/v2/status", methods=["GET"])
def status():
    return jsonify({
        "nombre": app.config["WHOAMI"],
        "version": app.config["VERSION"],
        "ambiente": app.config["ENV"],
        "debug": app.config["DEBUG"],
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "productos": "GET /api/v2/productos",
            "categorias": "GET /api/v2/categorias",
            "clientes": "POST /api/v2/clientes/mi-cliente",
            "inventario": "POST /api/v2/inventario/verificar",
            "carrito": "POST /api/v2/carrito/agregar",
            "pedidos": "POST /api/v2/pedidos/crear",
            "pagos_proxy": "POST /api/v2/pagos/procesar",
            "sistema_info": "GET /api/v2/sistema/info",
            "checkout": "POST /api/v2/checkout",
            "envios": "POST /api/v2/envios/crear",
        },
    }), 200


@app.route("/api/v2/sistema/info", methods=["GET"])
def sistema_info():
    """Endpoint JSON con información relevante del sistema.

    Incluye estado propio del microservicio, consumo del servicio aliado y
    datos adaptados de una API de terceros mediante Adapter.
    """
    payment_status = {
        "available": False,
        "status_code": None,
        "message": "No consultado",
    }

    try:
        payment_response = requests.get(f"{app.config['PAYMENT_SERVICE_URL']}/health", timeout=10)
        payment_status = {
            "available": payment_response.ok,
            "status_code": payment_response.status_code,
            "message": payment_response.json().get("service", "Servicio de pagos") if payment_response.ok else "Servicio no disponible",
        }
    except requests.RequestException as exc:
        payment_status = {
            "available": False,
            "status_code": None,
            "message": str(exc),
        }

    third_party_adapter = JsonPlaceholderAdapter()
    third_party_data = {
        "available": False,
        "message": "No consultado",
        "data": None,
    }

    try:
        third_party_payload = third_party_adapter.fetch()
        third_party_data = {
            "available": True,
            "message": "API de terceros consumida mediante Adapter",
            "data": third_party_payload,
        }
    except requests.RequestException as exc:
        third_party_data = {
            "available": False,
            "message": str(exc),
            "data": None,
        }

    return jsonify({
        "servicio": app.config["WHOAMI"],
        "version": app.config["VERSION"],
        "ambiente": app.config["ENV"],
        "timestamp": datetime.now().isoformat(),
        "resumen": {
            "productos": Producto.objects.count(),
            "clientes": Cliente.objects.count(),
            "pedidos": Pedido.objects.count(),
            "carritos": Carrito.objects.count(),
        },
        "servicio_aliado": payment_status,
        "api_terceros": third_party_data,
    }), 200


@app.route("/api/v2/pagos/procesar", methods=["POST"])
def procesar_pago_proxy_endpoint():
    """Proxy del core hacia el microservicio de pagos.

    Esto evita 404 cuando se prueba el core directamente sin pasar por Nginx.
    """
    try:
        payload = request.get_json(force=True) or {}

        response = requests.post(
            f"{app.config['PAYMENT_SERVICE_URL']}/api/v2/pagos/procesar",
            json=payload,
            timeout=20,
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "error": True,
                "mensaje": "Respuesta invalida del servicio de pagos",
            }

        return jsonify(data), response.status_code
    except requests.RequestException as exc:
        logger.exception("Error llamando el servicio de pagos")
        return error_response(f"Servicio de pagos no disponible: {exc}", 503)
    except Exception as exc:
        logger.exception("Error en proxy de pagos")
        return error_response(str(exc), 500)


@app.route("/api/v2/productos", methods=["GET"])
def listar_productos():
    productos = Producto.objects.all().order_by("nombre")
    return jsonify([serialize_producto(producto) for producto in productos]), 200


@app.route("/api/v2/productos/<int:producto_id>", methods=["GET"])
def detalle_producto(producto_id: int):
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return error_response("Producto no encontrado", 404)
    return jsonify(serialize_producto(producto)), 200


@app.route("/api/v2/categorias", methods=["GET"])
def listar_categorias():
    categorias = Categoria.objects.all().order_by("orden")
    return jsonify([serialize_categoria(categoria) for categoria in categorias]), 200


@app.route("/api/v2/clientes/mi-cliente", methods=["POST"])
def mi_cliente():
    try:
        payload = request.get_json(force=True) or {}
        cliente = obtener_cliente_por_payload(payload)
        return jsonify({"cliente": serialize_cliente(cliente), "creado": True}), 200
    except ValidationError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        logger.exception("Error en mi-cliente")
        return error_response(str(exc), 500)


@app.route("/api/v2/inventario/verificar", methods=["POST"])
def verificar_inventario_endpoint():
    try:
        payload = request.get_json(force=True) or {}
        producto_id = int(payload.get("producto_id"))
        cantidad = int(payload.get("cantidad", 1))
        inventario = Inventario.objects.get(producto_id=producto_id)
        disponible = inventario.cantidad_disponible >= cantidad
        return jsonify({
            "disponible": disponible,
            "cantidad_disponible": inventario.cantidad_disponible,
            "producto_id": producto_id,
        }), 200
    except Inventario.DoesNotExist:
        return jsonify({"disponible": False, "cantidad_disponible": 0}), 200
    except Exception as exc:
        logger.exception("Error verificando inventario")
        return error_response(str(exc), 500)


@app.route("/api/v2/inventario/reducir", methods=["PATCH"])
def reducir_inventario_endpoint():
    try:
        payload = request.get_json(force=True) or {}
        result = reducir_stock(int(payload.get("producto_id")), int(payload.get("cantidad", 1)))
        return jsonify(result), 200
    except ValidationError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        logger.exception("Error reduciendo inventario")
        return error_response(str(exc), 500)


@app.route("/api/v2/carrito/<int:cliente_id>", methods=["GET"])
def obtener_carrito_endpoint(cliente_id: int):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        carrito = obtener_o_crear_carrito(cliente)
        return jsonify(serialize_carrito(carrito)), 200
    except Cliente.DoesNotExist:
        return error_response("Cliente no encontrado", 404)


@app.route("/api/v2/carrito/agregar", methods=["POST"])
def agregar_carrito_endpoint():
    try:
        payload = request.get_json(force=True) or {}
        cliente = Cliente.objects.get(id=int(payload.get("cliente_id")))
        producto = Producto.objects.get(id=int(payload.get("producto_id")))
        cantidad = int(payload.get("cantidad", 1))
        if cantidad <= 0:
            raise ValidationError("Cantidad debe ser mayor a 0")

        validar_inventario(producto.id, cantidad)
        carrito = obtener_o_crear_carrito(cliente)
        CarritoItem.objects.update_or_create(
            carrito=carrito,
            producto=producto,
            defaults={"cantidad": cantidad},
        )
        return jsonify({"mensaje": "Producto agregado al carrito", "carrito": serialize_carrito(carrito)}), 200
    except (Cliente.DoesNotExist, Producto.DoesNotExist):
        return error_response("Cliente o producto no encontrado", 404)
    except ValidationError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        logger.exception("Error agregando al carrito")
        return error_response(str(exc), 500)


@app.route("/api/v2/carrito/<int:cliente_id>/eliminar/<int:producto_id>", methods=["DELETE"])
def eliminar_carrito_endpoint(cliente_id: int, producto_id: int):
    try:
        carrito = obtener_o_crear_carrito(Cliente.objects.get(id=cliente_id))
        CarritoItem.objects.filter(carrito=carrito, producto_id=producto_id).delete()
        return jsonify({"mensaje": "Producto eliminado del carrito", "carrito": serialize_carrito(carrito)}), 200
    except Cliente.DoesNotExist:
        return error_response("Cliente no encontrado", 404)


@app.route("/api/v2/carrito/<int:cliente_id>/vaciar", methods=["POST"])
def vaciar_carrito_endpoint(cliente_id: int):
    try:
        carrito = obtener_o_crear_carrito(Cliente.objects.get(id=cliente_id))
        CarritoItem.objects.filter(carrito=carrito).delete()
        return jsonify({"mensaje": "Carrito vaciado exitosamente"}), 200
    except Cliente.DoesNotExist:
        return error_response("Cliente no encontrado", 404)


@app.route("/api/v2/pedidos/crear", methods=["POST"])
def crear_pedido_endpoint():
    try:
        payload = request.get_json(force=True) or {}
        cliente_id = int(payload.get("cliente_id"))
        productos = payload.get("productos", [])
        usuario = obtener_usuario(payload.get("usuario"))
        pedido = crear_pedido_interno(cliente_id, productos, usuario=usuario)
        return jsonify({"mensaje": "Pedido creado", "pedido": serialize_pedido(pedido)}), 201
    except (Cliente.DoesNotExist, Producto.DoesNotExist):
        return error_response("Cliente o producto no encontrado", 404)
    except ValidationError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        logger.exception("Error creando pedido")
        return error_response(str(exc), 500)


@app.route("/api/v2/pedidos/<int:pedido_id>", methods=["GET"])
def detalle_pedido_endpoint(pedido_id: int):
    try:
        pedido = Pedido.objects.select_related("cliente", "usuario").get(id=pedido_id)
        return jsonify(serialize_pedido(pedido)), 200
    except Pedido.DoesNotExist:
        return error_response("Pedido no encontrado", 404)


@app.route("/api/v2/pedidos/<int:pedido_id>/cambiar-estado", methods=["PATCH"])
def cambiar_estado_pedido_endpoint(pedido_id: int):
    try:
        payload = request.get_json(force=True) or {}
        estado = payload.get("estado")
        if not estado:
            return error_response("estado es requerido", 400)
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = estado
        pedido.save(update_fields=["estado"])
        return jsonify({"mensaje": "Estado de pedido actualizado", "pedido": serialize_pedido(pedido)}), 200
    except Pedido.DoesNotExist:
        return error_response("Pedido no encontrado", 404)


@app.route("/api/v2/envios/crear", methods=["POST"])
def crear_envio_endpoint():
    try:
        payload = request.get_json(force=True) or {}
        pedido = Pedido.objects.get(id=int(payload.get("pedido_id")))
        envio = Envio.objects.create(
            pedido=pedido,
            direccion_entrega=payload.get("direccion_entrega", "Por definir"),
            estado_envio="Preparando",
        )
        return jsonify({"mensaje": "Envío creado", "envio": serialize_envio(envio)}), 201
    except Pedido.DoesNotExist:
        return error_response("Pedido no encontrado", 404)


@app.route("/api/v2/envios/<int:envio_id>/actualizar", methods=["PATCH"])
def actualizar_envio_endpoint(envio_id: int):
    try:
        payload = request.get_json(force=True) or {}
        nuevo_estado = payload.get("nuevo_estado")
        if not nuevo_estado:
            return error_response("nuevo_estado es requerido", 400)
        envio = Envio.objects.get(id=envio_id)
        envio.estado_envio = nuevo_estado
        envio.save(update_fields=["estado_envio"])
        return jsonify({"mensaje": "Estado de envío actualizado", "envio": serialize_envio(envio)}), 200
    except Envio.DoesNotExist:
        return error_response("Envío no encontrado", 404)


@app.route("/api/v2/checkout", methods=["POST"])
def checkout_endpoint():
    try:
        payload = request.get_json(force=True) or {}
        cliente_id = int(payload.get("cliente_id"))
        metodo_pago = payload.get("metodo_pago", "Transferencia")
        direccion_entrega = payload.get("direccion_entrega", "Por definir")
        usuario = obtener_usuario(payload.get("usuario"))

        carrito = obtener_o_crear_carrito(Cliente.objects.get(id=cliente_id))
        items = list(carrito.items.select_related("producto").all())
        if not items:
            return error_response("El carrito está vacío", 400)

        productos = [{"producto_id": item.producto_id, "cantidad": item.cantidad} for item in items]
        pedido = crear_pedido_interno(cliente_id, productos, usuario=usuario)

        if metodo_pago == "Pago Adelantado":
            descuento = pedido.total * Decimal("0.03")
            pedido.total -= descuento
            pedido.save(update_fields=["total"])

        import requests

        pago_response = requests.post(
            f"{app.config['PAYMENT_SERVICE_URL']}/api/v2/pagos/procesar",
            json={"pedido_id": pedido.id, "monto": float(pedido.total), "metodo_pago": metodo_pago},
            timeout=20,
        )
        pago_response.raise_for_status()
        pago_data = pago_response.json()

        envio = Envio.objects.create(
            pedido=pedido,
            direccion_entrega=direccion_entrega,
            estado_envio="Preparando",
        )

        return jsonify({
            "mensaje": "Compra procesada exitosamente",
            "compra": {
                "pedido": serialize_pedido(pedido),
                "pago": pago_data,
                "envio": serialize_envio(envio),
            },
        }), 201
    except Cliente.DoesNotExist:
        return error_response("Cliente no encontrado", 404)
    except ValidationError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        logger.exception("Error en checkout")
        return error_response(str(exc), 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")), debug=app.config["DEBUG"])
