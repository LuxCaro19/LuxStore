from django import template

register = template.Library()


@register.filter(name="peso")
def peso(value):
    """
    Formatea un número entero como moneda chilena ($15.000).
    """
    if value is None or value == "":
        return "$0"
    try:
        val = int(value)
        return f"${val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return f"${value}"
