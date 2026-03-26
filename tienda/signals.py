from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cliente, Envio


@receiver(post_save, sender=Cliente)
def actualizar_envios_al_cambiar_direccion(sender, instance, created, **kwargs):
    """
    Signal que actualiza automáticamente la dirección de envío cuando 
    el cliente cambia su dirección, pero solo para envíos en estado "Preparando"
    (aún no enviados).
    
    Argumentos:
        - sender: Modelo Cliente
        - instance: Instancia del Cliente que fue guardada
        - created: Boolean, True si es un registro nuevo, False si es actualización
    """
    # No hacer nada si es un nuevo cliente (recién creado)
    if created:
        return
    
    # Obtener todos los envíos del cliente que aún estén en estado "Preparando"
    envios_pendientes = Envio.objects.filter(
        pedido__cliente=instance,
        estado_envio="Preparando"  # Solo los que aún no han sido enviados
    )
    
    # Actualizar la dirección de cada envío
    for envio in envios_pendientes:
        envio.direccion_entrega = instance.direccion
        envio.save()
