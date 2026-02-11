import os

class EmailNotifierMock:
    def enviar(self, pedido):
        print("EMAIL MOCK: Pedido creado", pedido.id)

class EmailNotifierReal:
    def enviar(self, pedido):
        print("EMAIL REAL enviado")  

class NotificadorFactory:
    @staticmethod
    def crear_notificador():
        if os.getenv("ENV_TYPE") == "PROD":
            return EmailNotifierReal()
        return EmailNotifierMock()
