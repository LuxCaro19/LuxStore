from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import PerfilUsuario
from .forms import LoginForm, UsuarioCrearForm, UsuarioEditarForm
from .decorators import admin_required


def login_view(request):
    """
    Vista de inicio de sesión de LuxStore.
    Si el usuario ya tiene sesión activa, lo envía directo al Punto de Venta.
    """
    if request.user.is_authenticated:
        return redirect("ventas:pos")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido/a, {user.first_name or user.username}!")

            # Redirigir a 'next' o al POS
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("ventas:pos")
        else:
            messages.error(request, "Usuario o contraseña incorrectos. Revisa tus datos.")
    else:
        form = LoginForm()

    return render(request, "usuarios/login.html", {"form": form})


def logout_view(request):
    """
    Cierra la sesión del usuario actual y lo redirige al login.
    """
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("usuarios:login")


@admin_required
def lista_usuarios(request):
    """
    Panel administrativo: listado de usuarios con roles y estados.
    """
    usuarios = (
        User.objects.select_related("perfil")
        .order_by("-is_superuser", "username")
    )
    return render(request, "usuarios/lista.html", {"usuarios": usuarios})


@admin_required
def crear_usuario(request):
    """
    Crea un nuevo usuario en el sistema asignándole rol de Admin o Visita.
    """
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            nuevo_user = form.save()
            messages.success(
                request,
                f"Usuario '{nuevo_user.username}' ({nuevo_user.perfil.get_rol_display()}) creado exitosamente."
            )
            return redirect("usuarios:lista")
    else:
        form = UsuarioCrearForm()

    return render(
        request,
        "usuarios/form.html",
        {
            "form": form,
            "titulo": "Nuevo usuario",
            "accion": "Crear usuario",
        },
    )


@admin_required
def editar_usuario(request, pk):
    """
    Edita un usuario existente: rol, nombre, teléfono, estado activo y contraseña opcional.
    """
    usuario = get_object_or_404(User.objects.select_related("perfil"), pk=pk)

    # Evitar que el admin se desactive a sí mismo
    if request.method == "POST":
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            if usuario == request.user and not form.cleaned_data.get("is_active"):
                messages.error(request, "No puedes desactivar tu propia cuenta activa.")
                return redirect("usuarios:lista")

            form.save()
            messages.success(request, f"Usuario '{usuario.username}' actualizado correctamente.")
            return redirect("usuarios:lista")
    else:
        form = UsuarioEditarForm(instance=usuario)

    return render(
        request,
        "usuarios/form.html",
        {
            "form": form,
            "usuario": usuario,
            "titulo": f"Editar usuario: {usuario.username}",
            "accion": "Guardar cambios",
        },
    )


@require_POST
@admin_required
def eliminar_usuario(request, pk):
    """
    Elimina un usuario del sistema (no permitido sobre sí mismo).
    """
    usuario = get_object_or_404(User, pk=pk)
    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect("usuarios:lista")

    nombre = usuario.username
    usuario.delete()
    messages.success(request, f"Usuario '{nombre}' eliminado del sistema.")
    return redirect("usuarios:lista")
