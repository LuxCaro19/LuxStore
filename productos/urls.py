from django.urls import path

from . import views


app_name = "productos"

urlpatterns = [
    path("", views.lista_productos, name="lista"),
    path("nuevo/", views.crear_producto, name="crear"),
    path("<int:pk>/editar/", views.editar_producto, name="editar"),
    path("inventario/", views.inventario, name="inventario"),
    path("inventario/exportar-excel/", views.exportar_inventario_excel, name="exportar_excel"),
    path("<int:pk>/ajustar-stock/", views.ajustar_stock, name="ajustar_stock"),
]
