import json
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from productos.models import Producto
from .models import Venta, DetalleVenta
from django.db.models import Sum
from django.utils import timezone
from fiadores.models import Fiador
from fiadores.models import Fiador, MovimientoFiado


def pos(request):
    fiadores = Fiador.objects.filter(
        activo=True
    ).order_by("nombre")

    fiadores_data = [
        {
            "id": fiador.id,
            "nombre": fiador.nombre,
            "saldo": fiador.saldo,
        }
        for fiador in fiadores
    ]

    return render(
        request,
        "ventas/pos.html",
        {
            "fiadores": fiadores,
            "fiadores_data": fiadores_data,
        },
    )


def buscar_productos(request):
    busqueda = request.GET.get("q", "").strip()

    if not busqueda:
        return JsonResponse({
            "productos": []
        })

    producto_codigo = Producto.objects.filter(
        activo=True,
        codigo_barras=busqueda,
    ).first()

    if producto_codigo:
        productos = [producto_codigo]

    else:
        productos = Producto.objects.filter(
            activo=True
        ).filter(
            Q(nombre__icontains=busqueda)
            | Q(codigo_barras__icontains=busqueda)
        )[:8]

    resultados = [
        {
            "id": producto.id,
            "nombre": producto.nombre,
            "codigo_barras": producto.codigo_barras,
            "precio": producto.precio,
            "stock_actual": producto.stock_actual,
            "stock_minimo": producto.stock_minimo,
        }
        for producto in productos
    ]

    return JsonResponse({
        "productos": resultados
    })


def confirmar_venta(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido.",
            },
            status=405,
        )

    try:
        datos = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Los datos enviados no son válidos.",
            },
            status=400,
        )

    items = datos.get("items", [])

    es_fiado = bool(
    datos.get("fiado", False)
    )

    fiador_id = datos.get(
        "fiador_id"
    )

    if not items:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La venta no tiene productos.",
            },
            status=400,
        )

    # Consolidamos cantidades por producto.
    cantidades = {}

    try:
        for item in items:
            producto_id = int(item["id"])
            cantidad = int(item["cantidad"])

            if cantidad <= 0:
                raise ValueError

            cantidades[producto_id] = (
                cantidades.get(producto_id, 0)
                + cantidad
            )

    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La venta contiene productos inválidos.",
            },
            status=400,
        )

    try:

        fiador = None

        if es_fiado:

            if not fiador_id:
                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": "Debes seleccionar un fiador.",
                    },
                    status=400,
                )

            try:

                fiador = Fiador.objects.get(
                    pk=fiador_id,
                    activo=True,
                )

            except Fiador.DoesNotExist:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": "El fiador seleccionado no es válido.",
                    },
                    status=400,
                )

        with transaction.atomic():

            productos = Producto.objects.select_for_update().filter(
                id__in=cantidades.keys(),
                activo=True,
            )

            productos = {
                producto.id: producto
                for producto in productos
            }

            if len(productos) != len(cantidades):
                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": "Uno o más productos ya no están disponibles.",
                    },
                    status=400,
                )

            total = 0
            detalles = []

            # Validación de stock y cálculo real del total.
            for producto_id, cantidad in cantidades.items():

                producto = productos[producto_id]

                if producto.stock_actual < cantidad:
                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                f"Stock insuficiente para "
                                f"{producto.nombre}. "
                                f"Disponible: {producto.stock_actual}."
                            ),
                        },
                        status=400,
                    )

                subtotal = producto.precio * cantidad
                total += subtotal

                detalles.append(
                    {
                        "producto": producto,
                        "cantidad": cantidad,
                        "precio_unitario": producto.precio,
                    }
                )

            # Creamos la cabecera.
            venta = Venta.objects.create(
                total=total,
                estado=Venta.Estado.COMPLETADA,
            )

            # Creamos detalles y descontamos stock.
            for detalle in detalles:

                producto = detalle["producto"]
                cantidad = detalle["cantidad"]

                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=detalle["precio_unitario"],
                )

                producto.stock_actual -= cantidad

                producto.save(
                    update_fields=[
                        "stock_actual",
                        "actualizado_en",
                    ]
                )

            if es_fiado:

                MovimientoFiado.objects.create(
                    fiador=fiador,
                    venta=venta,
                    tipo=MovimientoFiado.Tipo.CARGO,
                    monto=venta.total,
                    nota="Venta fiada",
                )

    except Exception:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "No fue posible registrar la venta.",
            },
            status=500,
        )

    return JsonResponse({
        "ok": True,
        "venta_id": venta.id,
        "total": venta.total,
        "mensaje": "Venta registrada correctamente.",
    })


def corte_diario(request):
    hoy = timezone.localdate()

    ventas = Venta.objects.filter(
        estado=Venta.Estado.COMPLETADA,
        creada_en__date=hoy,
    ).order_by("-creada_en")

    cantidad_ventas = ventas.count()

    total_vendido = (
        ventas.aggregate(total=Sum("total"))["total"]
        or 0
    )

    ultimas_ventas = ventas[:10]

    return render(
        request,
        "ventas/corte_diario.html",
        {
            "hoy": hoy,
            "cantidad_ventas": cantidad_ventas,
            "total_vendido": total_vendido,
            "ultimas_ventas": ultimas_ventas,
        },
    )