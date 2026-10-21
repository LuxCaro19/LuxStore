from django.urls import path

from . import views


app_name = "fiadores"


urlpatterns = [
    path("", views.lista_fiadores, name="lista"),
    path("nuevo/", views.crear_fiador, name="crear"),
    path("crear-rapido/", views.crear_fiador_rapido, name="crear_rapido"),

    path(
        "<int:pk>/",
        views.detalle_fiador,
        name="detalle",
    ),

    path(
        "<int:pk>/abono/",
        views.registrar_abono,
        name="registrar_abono",
    ),
]