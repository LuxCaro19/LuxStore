from django.contrib import admin

from .models import Fiador, MovimientoFiado


class MovimientoFiadoInline(admin.TabularInline):
    model = MovimientoFiado
    extra = 0
    readonly_fields = (
        "tipo",
        "monto",
        "venta",
        "creado_en",
    )


@admin.register(Fiador)
class FiadorAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "saldo_actual",
        "activo",
    )

    search_fields = (
        "nombre",
    )

    list_filter = (
        "activo",
    )

    inlines = [
        MovimientoFiadoInline,
    ]

    @admin.display(description="Deuda")
    def saldo_actual(self, obj):
        return f"${obj.saldo}"


@admin.register(MovimientoFiado)
class MovimientoFiadoAdmin(admin.ModelAdmin):
    list_display = (
        "fiador",
        "tipo",
        "monto",
        "venta",
        "creado_en",
    )

    list_filter = (
        "tipo",
        "creado_en",
    )