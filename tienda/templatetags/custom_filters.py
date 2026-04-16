from django import template

register = template.Library()

@register.filter
def format_precio(value):
    """Formatea un precio con separadores de miles al estilo colombiano."""
    try:
        # Convertir a entero para eliminar decimales
        valor_int = int(float(value))
        # Formatear con separador de miles
        return f"{valor_int:,}".replace(',', "'")
    except (ValueError, TypeError):
        return value
