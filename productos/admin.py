from django.contrib import admin

from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "codigo_barras",
        "precio",
        "stock_actual",
        "stock_minimo",
        "activo",
    )

    search_fields = (
        "nombre",
        "codigo_barras",
    )

    list_filter = (
        "activo",
    )