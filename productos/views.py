from django.db.models import Q
from django.shortcuts import redirect, render

from .forms import ProductoForm
from .models import Producto


def lista_productos(request):
    busqueda = request.GET.get("q", "").strip()

    productos = Producto.objects.all()

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(codigo_barras__icontains=busqueda)
        )

    context = {
        "productos": productos,
        "busqueda": busqueda,
    }

    return render(request, "productos/lista.html", context)


def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("productos:lista")

    else:
        form = ProductoForm()

    return render(
        request,
        "productos/crear.html",
        {
            "form": form,
        },
    )