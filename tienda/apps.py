from django.apps import AppConfig


class TiendaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tienda'
    
    def ready(self):
        """Registrar signals cuando la app se inicializa"""
        import tienda.signals  # noqa
