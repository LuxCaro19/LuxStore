from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from usuarios import views as usuarios_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Autenticación principal
    path("login/", usuarios_views.login_view, name="login"),
    path("logout/", usuarios_views.logout_view, name="logout"),

    path(
        "",
        RedirectView.as_view(
            pattern_name="ventas:pos",
            permanent=False,
        ),
    ),

    path(
        "productos/",
        include("productos.urls"),
    ),

    path(
        "ventas/",
        include("ventas.urls"),
    ),

    path(
        "fiadores/",
        include("fiadores.urls"),
    ),

    path(
        "usuarios/",
        include("usuarios.urls"),
    ),

    path(
        "configuracion/",
        include("configuracion.urls"),
    ),
]
