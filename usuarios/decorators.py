from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings


def admin_required(view_func):
    """
    Decorador que restringe el acceso exclusivamente a usuarios con rol Administrador.
    Si el usuario no ha iniciado sesión, redirige al login.
    Si el usuario tiene rol Visita, redirige al Punto de Venta (POS) con un mensaje informativo.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        es_admin = (
            request.user.is_superuser
            or (hasattr(request.user, "perfil") and request.user.perfil.es_admin)
        )

        if not es_admin:
            messages.warning(
                request,
                "Acceso restringido: Esta sección requiere perfil de Administrador."
            )
            return redirect("ventas:pos")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
