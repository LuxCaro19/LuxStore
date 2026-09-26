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
]