from django.shortcuts import render, redirect
from django.contrib import messages
from usuarios.decorators import admin_required

from .models import ConfiguracionNegocio
from .forms import ConfiguracionNegocioForm


@admin_required
def configuracion_index(request):
    """
    Vista administrativa para consultar y editar los datos comerciales de la tienda
    y las preferencias del ticket térmico.
    """
    config = ConfiguracionNegocio.obtener_configuracion()

    if request.method == "POST":
        form = ConfiguracionNegocioForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración del negocio guardada exitosamente.")
            return redirect("configuracion:index")
    else:
        form = ConfiguracionNegocioForm(instance=config)

    return render(
        request,
        "configuracion/index.html",
        {
            "form": form,
            "config": config,
        },
    )
