from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Optional

import requests


class MicroserviceClientError(RuntimeError):
    pass


class MicroserviceClient:
    def __init__(self) -> None:
        self.core_base_url = os.getenv("HABITE_CORE_SERVICE_URL", "http://flask_core:5001").rstrip("/")
        self.payment_base_url = os.getenv("HABITE_PAYMENT_SERVICE_URL", "http://flask_payment:5000").rstrip("/")
        self.timeout = int(os.getenv("HABITE_SERVICE_TIMEOUT", "20"))

    def _request_json(self, method: str, base_url: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{base_url}{path}"
        try:
            response = requests.request(method, url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise MicroserviceClientError(str(exc)) from exc

        if not response.content:
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise MicroserviceClientError(f"Respuesta no JSON desde {url}") from exc

    def _request_binary(self, method: str, base_url: str, path: str, payload: Optional[Dict[str, Any]] = None) -> bytes:
        url = f"{base_url}{path}"
        try:
            response = requests.request(method, url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise MicroserviceClientError(str(exc)) from exc

        return response.content

    def verificar_inventario(self, producto_id: int, cantidad: int) -> bool:
        data = self._request_json("post", self.core_base_url, "/api/v2/inventario/verificar", {
            "producto_id": producto_id,
            "cantidad": cantidad,
        })
        return bool(data.get("disponible", False))

    def reducir_stock(self, producto_id: int, cantidad: int) -> Dict[str, Any]:
        return self._request_json("patch", self.core_base_url, "/api/v2/inventario/reducir", {
            "producto_id": producto_id,
            "cantidad": cantidad,
        })

    def crear_pedido(self, cliente_id: int, productos_data: Iterable[tuple[int, int]], usuario: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request_json("post", self.core_base_url, "/api/v2/pedidos/crear", {
            "cliente_id": cliente_id,
            "productos": [
                {"producto_id": producto_id, "cantidad": cantidad}
                for producto_id, cantidad in productos_data
            ],
            "usuario": usuario,
        })

    def actualizar_estado_pedido(self, pedido_id: int, nuevo_estado: str) -> Dict[str, Any]:
        return self._request_json("patch", self.core_base_url, f"/api/v2/pedidos/{pedido_id}/cambiar-estado", {
            "estado": nuevo_estado,
        })

    def obtener_pedido(self, pedido_id: int) -> Dict[str, Any]:
        return self._request_json("get", self.core_base_url, f"/api/v2/pedidos/{pedido_id}")

    def obtener_o_crear_cliente(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request_json("post", self.core_base_url, "/api/v2/clientes/mi-cliente", payload)

    def obtener_carrito(self, cliente_id: int) -> Dict[str, Any]:
        return self._request_json("get", self.core_base_url, f"/api/v2/carrito/{cliente_id}")

    def agregar_al_carrito(self, cliente_id: int, producto_id: int, cantidad: int) -> Dict[str, Any]:
        return self._request_json("post", self.core_base_url, "/api/v2/carrito/agregar", {
            "cliente_id": cliente_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
        })

    def eliminar_del_carrito(self, cliente_id: int, producto_id: int) -> Dict[str, Any]:
        return self._request_json("delete", self.core_base_url, f"/api/v2/carrito/{cliente_id}/eliminar/{producto_id}")

    def vaciar_carrito(self, cliente_id: int) -> Dict[str, Any]:
        return self._request_json("post", self.core_base_url, f"/api/v2/carrito/{cliente_id}/vaciar")

    def checkout_carrito(self, cliente_id: int, metodo_pago: str, direccion_entrega: str, usuario: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request_json("post", self.core_base_url, "/api/v2/checkout", {
            "cliente_id": cliente_id,
            "metodo_pago": metodo_pago,
            "direccion_entrega": direccion_entrega,
            "usuario": usuario,
        })

    def crear_envio(self, pedido_id: int, direccion_entrega: str) -> Dict[str, Any]:
        return self._request_json("post", self.core_base_url, "/api/v2/envios/crear", {
            "pedido_id": pedido_id,
            "direccion_entrega": direccion_entrega,
        })

    def actualizar_envio(self, envio_id: int, nuevo_estado: str) -> Dict[str, Any]:
        return self._request_json("patch", self.core_base_url, f"/api/v2/envios/{envio_id}/actualizar", {
            "nuevo_estado": nuevo_estado,
        })

    def procesar_pago(self, pedido_id: int, metodo_pago: str, monto: Any) -> Dict[str, Any]:
        return self._request_json("post", self.payment_base_url, "/api/v2/pagos/procesar", {
            "pedido_id": pedido_id,
            "metodo_pago": metodo_pago,
            "monto": float(monto),
        })

    def generar_factura(self, pedido_payload: Dict[str, Any]) -> bytes:
        return self._request_binary("post", self.payment_base_url, "/api/v2/facturas/generar", {
            "pedido": pedido_payload,
        })


client = MicroserviceClient()
