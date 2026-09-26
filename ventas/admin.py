from django.contrib import admin

from .models import DetalleVenta, Venta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = (
        "producto",
        "cantidad",
        "precio_unitario",
    )


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "total",
        "estado",
        "creada_en",
    )

    list_filter = (
        "estado",
        "creada_en",
    )

    date_hierarchy = "creada_en"

    inlines = [
        DetalleVentaInline,
    ]