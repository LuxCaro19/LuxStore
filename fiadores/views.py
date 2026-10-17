from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import FiadorForm
from .models import Fiador, MovimientoFiado


def lista_fiadores(request):
    busqueda = request.GET.get("q", "").strip()

    fiadores = Fiador.objects.all().order_by("nombre")

    if busqueda:
        fiadores = fiadores.filter(
            Q(nombre__icontains=busqueda)
        )

    return render(
        request,
        "fiadores/lista.html",
        {
            "fiadores": fiadores,
            "busqueda": busqueda,
        },
    )


def crear_fiador(request):

    if request.method == "POST":

        form = FiadorForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect(
                "fiadores:lista"
            )

    else:

        form = FiadorForm(
            initial={
                "activo": True,
            }
        )

    return render(
        request,
        "fiadores/crear.html",
        {
            "form": form,
        },
    )

def detalle_fiador(request, pk):
    fiador = get_object_or_404(
        Fiador,
        pk=pk,
    )

    movimientos = (
        fiador.movimientos
        .select_related("venta")
        .all()
    )

    return render(
        request,
        "fiadores/detalle.html",
        {
            "fiador": fiador,
            "movimientos": movimientos,
        },
    )


def registrar_abono(request, pk):

    if request.method != "POST":
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido.",
            },
            status=405,
        )

    try:

        with transaction.atomic():

            fiador = (
                Fiador.objects
                .select_for_update()
                .get(pk=pk)
            )

            try:
                monto = int(
                    request.POST.get(
                        "monto",
                        ""
                    )
                )

            except (TypeError, ValueError):
                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": "Ingresa un monto válido.",
                    },
                    status=400,
                )

            nota = request.POST.get(
                "nota",
                ""
            ).strip()


            if monto <= 0:
                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": "El abono debe ser mayor a $0.",
                    },
                    status=400,
                )


            saldo_actual = fiador.saldo


            if saldo_actual <= 0:
                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": "Este fiador no tiene deuda pendiente.",
                    },
                    status=400,
                )


            if monto > saldo_actual:
                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El abono no puede ser mayor "
                            "a la deuda actual."
                        ),
                    },
                    status=400,
                )


            movimiento = MovimientoFiado.objects.create(
                fiador=fiador,
                tipo=MovimientoFiado.Tipo.ABONO,
                monto=monto,
                nota=nota,
            )


            nuevo_saldo = fiador.saldo


    except Fiador.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Fiador no encontrado.",
            },
            status=404,
        )


    fecha = timezone.localtime(
        movimiento.creado_en
    ).strftime("%d/%m/%Y %H:%M")


    return JsonResponse(
        {
            "ok": True,
            "mensaje": "Abono registrado",
            "saldo": nuevo_saldo,
            "movimiento": {
                "id": movimiento.id,
                "monto": movimiento.monto,
                "nota": movimiento.nota,
                "fecha": fecha,
            },
        }
    )