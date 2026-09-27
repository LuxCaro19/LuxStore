from django.db.models import F, Q
from .forms import ProductoForm
from .models import Producto
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render


from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductoForm
from .models import Producto


def lista_productos(request):
    busqueda = request.GET.get("q", "").strip()

    productos = Producto.objects.all().order_by("nombre")

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(codigo_barras__icontains=busqueda)
        )

    return render(
        request,
        "productos/lista.html",
        {
            "productos": productos,
            "busqueda": busqueda,
        },
    )


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


def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        form = ProductoForm(
            request.POST,
            instance=producto,
        )

        if form.is_valid():
            producto = form.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "ok": True,
                        "mensaje": "Cambios guardados",
                        "producto": {
                            "id": producto.id,
                            "nombre": producto.nombre,
                            "codigo_barras": producto.codigo_barras,
                            "precio": producto.precio,
                            "stock_actual": producto.stock_actual,
                            "stock_minimo": producto.stock_minimo,
                            "activo": producto.activo,
                        },
                    }
                )

            return redirect(
                "productos:editar",
                pk=producto.pk,
            )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            errores = {
                campo: [
                    error["message"]
                    for error in lista
                ]
                for campo, lista in form.errors.get_json_data().items()
            }

            return JsonResponse(
                {
                    "ok": False,
                    "errores": errores,
                },
                status=400,
            )

    else:
        form = ProductoForm(instance=producto)

    return render(
        request,
        "productos/editar.html",
        {
            "form": form,
            "producto": producto,
        },
    )


def inventario(request):
    busqueda = request.GET.get("q", "").strip()

    productos = Producto.objects.filter(
        activo=True
    ).order_by("nombre")

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(codigo_barras__icontains=busqueda)
        )

    total_productos = Producto.objects.filter(
        activo=True
    ).count()

    productos_quiebre = Producto.objects.filter(
        activo=True,
        stock_actual__lte=F("stock_minimo"),
    ).count()

    productos_sin_stock = Producto.objects.filter(
        activo=True,
        stock_actual=0,
    ).count()

    return render(
        request,
        "productos/inventario.html",
        {
            "productos": productos,
            "busqueda": busqueda,
            "total_productos": total_productos,
            "productos_quiebre": productos_quiebre,
            "productos_sin_stock": productos_sin_stock,
        },
    )