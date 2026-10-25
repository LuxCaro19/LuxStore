from django.urls import path

from . import views


app_name = "ventas"

urlpatterns = [
    path("", views.pos, name="pos"),

    path(
        "buscar-productos/",
        views.buscar_productos,
        name="buscar_productos",
    ),

    path(
        "confirmar/",
        views.confirmar_venta,
        name="confirmar_venta",
    ),

    path(
        "corte-diario/",
        views.corte_diario,
        name="corte_diario",
    ),

    path(
        "cerrar-caja/",
        views.cerrar_caja,
        name="cerrar_caja",
    ),

    path(
        "historial/",
        views.historial_ventas,
        name="historial",
    ),

    path(
        "<int:pk>/ticket/",
        views.ticket_venta,
        name="ticket_venta",
    ),
]