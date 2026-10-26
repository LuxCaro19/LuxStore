from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.lista_usuarios, name="lista"),
    path("nuevo/", views.crear_usuario, name="crear"),
    path("<int:pk>/editar/", views.editar_usuario, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar_usuario, name="eliminar"),
]
