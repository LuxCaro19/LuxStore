import os
import json
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from productos.models import Producto
from .models import Venta, DetalleVenta, CierreCaja
from django.utils import timezone
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

    medio_pago = str(datos.get("medio_pago", "")).strip().upper()
    es_fiado = bool(datos.get("fiado", False))

    if es_fiado or medio_pago == Venta.MedioPago.FIADO:
        medio_pago = Venta.MedioPago.FIADO
        es_fiado = True
    elif medio_pago == Venta.MedioPago.TARJETA:
        medio_pago = Venta.MedioPago.TARJETA
    elif medio_pago == Venta.MedioPago.TRANSFERENCIA:
        medio_pago = Venta.MedioPago.TRANSFERENCIA
    else:
        medio_pago = Venta.MedioPago.EFECTIVO

    fiador_id = datos.get(
        "fiador_id"
    )

    monto_recibido_raw = datos.get("monto_recibido")
    monto_recibido = None
    if medio_pago == Venta.MedioPago.EFECTIVO and monto_recibido_raw not in (None, ""):
        try:
            monto_recibido = int(monto_recibido_raw)
            if monto_recibido < 0:
                raise ValueError
        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "El monto recibido no es válido.",
                },
                status=400,
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

            # Validación del monto recibido si es en efectivo
            if medio_pago == Venta.MedioPago.EFECTIVO and monto_recibido is not None:
                if monto_recibido < total:
                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": f"El monto recibido (${monto_recibido:,}) es menor al total (${total:,}).".replace(",", "."),
                        },
                        status=400,
                    )

            # Creamos la cabecera.
            venta = Venta.objects.create(
                total=total,
                estado=Venta.Estado.COMPLETADA,
                medio_pago=medio_pago,
                monto_recibido=monto_recibido,
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
        "medio_pago": venta.medio_pago,
        "monto_recibido": venta.monto_recibido,
        "vuelto": venta.vuelto,
        "mensaje": "Venta registrada correctamente.",
    })


def corte_diario(request):
    hoy = timezone.localdate()

    ventas = Venta.objects.filter(
        estado=Venta.Estado.COMPLETADA,
        creada_en__date=hoy,
    ).order_by("-creada_en")

    cantidad_ventas = ventas.count()

    # Total efectivo percibido hoy
    total_efectivo = (
        ventas.filter(medio_pago=Venta.MedioPago.EFECTIVO)
        .aggregate(total=Sum("total"))["total"]
        or 0
    )

    # Total cobrado con tarjeta hoy
    total_tarjeta = (
        ventas.filter(medio_pago=Venta.MedioPago.TARJETA)
        .aggregate(total=Sum("total"))["total"]
        or 0
    )

    # Total efectivamente ingresado (Efectivo + Tarjeta)
    total_percibido = total_efectivo + total_tarjeta

    # Total fiado del día (cuentas por cobrar, no es dinero en caja hoy)
    total_fiado = (
        ventas.filter(medio_pago=Venta.MedioPago.FIADO)
        .aggregate(total=Sum("total"))["total"]
        or 0
    )

    # Total general bruto vendido
    total_vendido = (
        ventas.aggregate(total=Sum("total"))["total"]
        or 0
    )

    ultimas_ventas = ventas[:25]

    # Verificar si ya existe un cierre de caja registrado hoy
    ultimo_cierre = CierreCaja.objects.filter(fecha=hoy).first()

    return render(
        request,
        "ventas/corte_diario.html",
        {
            "hoy": hoy,
            "cantidad_ventas": cantidad_ventas,
            "total_vendido": total_vendido,
            "total_efectivo": total_efectivo,
            "total_tarjeta": total_tarjeta,
            "total_percibido": total_percibido,
            "total_fiado": total_fiado,
            "ultimas_ventas": ultimas_ventas,
            "ultimo_cierre": ultimo_cierre,
        },
    )


def cerrar_caja(request):
    """
    Endpoint POST (fetch JSON) para registrar el cierre de caja del día con cuadratura de efectivo.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "mensaje": "Método no permitido."}, status=405)

    try:
        datos = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "mensaje": "Datos no válidos."}, status=400)

    try:
        efectivo_real = int(datos.get("efectivo_real", ""))
        if efectivo_real < 0:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse(
            {"ok": False, "mensaje": "Ingresa un monto de efectivo válido (igual o mayor a $0)."},
            status=400,
        )

    nota = str(datos.get("nota", "")).strip()
    hoy = timezone.localdate()

    ventas = Venta.objects.filter(
        estado=Venta.Estado.COMPLETADA,
        creada_en__date=hoy,
    )

    cantidad_ventas = ventas.count()

    total_efectivo = (
        ventas.filter(medio_pago=Venta.MedioPago.EFECTIVO)
        .aggregate(total=Sum("total"))["total"]
        or 0
    )

    total_tarjeta = (
        ventas.filter(medio_pago=Venta.MedioPago.TARJETA)
        .aggregate(total=Sum("total"))["total"]
        or 0
    )

    total_fiado = (
        ventas.filter(medio_pago=Venta.MedioPago.FIADO)
        .aggregate(total=Sum("total"))["total"]
        or 0
    )

    total_vendido = (
        ventas.aggregate(total=Sum("total"))["total"]
        or 0
    )

    diferencia = efectivo_real - total_efectivo

    with transaction.atomic():
        cierre = CierreCaja.objects.create(
            fecha=hoy,
            cantidad_ventas=cantidad_ventas,
            total_efectivo_sistema=total_efectivo,
            total_tarjeta_sistema=total_tarjeta,
            total_fiado_sistema=total_fiado,
            total_vendido=total_vendido,
            efectivo_real=efectivo_real,
            diferencia=diferencia,
            nota=nota,
        )

    return JsonResponse(
        {
            "ok": True,
            "mensaje": "Cierre de caja registrado exitosamente.",
            "cierre": {
                "id": cierre.id,
                "hora": timezone.localtime(cierre.cerrado_en).strftime("%H:%M"),
                "efectivo_real": cierre.efectivo_real,
                "diferencia": cierre.diferencia,
            },
        }
    )


def ticket_venta(request, pk):
    """
    Vista optimizada para impresión de ticket térmico (58mm / 80mm).
    Comprobante interno no válido como boleta.
    """
    venta = get_object_or_404(
        Venta.objects.prefetch_related("detalles__producto"),
        pk=pk,
    )

    fiador = None
    if venta.medio_pago == Venta.MedioPago.FIADO:
        movimiento = venta.movimientos_fiados.select_related("fiador").first()
        if movimiento:
            fiador = movimiento.fiador

    negocio_nombre = os.getenv("TICKET_NEGOCIO_NOMBRE", "LUXSTORE")
    negocio_direccion = os.getenv("TICKET_NEGOCIO_DIRECCION", "")
    negocio_telefono = os.getenv("TICKET_NEGOCIO_TELEFONO", "")
    negocio_rut = os.getenv("TICKET_NEGOCIO_RUT", "")

    ancho_mm = request.GET.get("ancho", os.getenv("TICKET_ANCHO_MM", "58")).strip()
    if ancho_mm not in ("58", "80"):
        ancho_mm = "58"

    autoprint = request.GET.get("autoprint", "0") in ("1", "true")

    total_articulos = sum(d.cantidad for d in venta.detalles.all())

    context = {
        "venta": venta,
        "detalles": venta.detalles.all(),
        "fiador": fiador,
        "total_articulos": total_articulos,
        "negocio_nombre": negocio_nombre,
        "negocio_direccion": negocio_direccion,
        "negocio_telefono": negocio_telefono,
        "negocio_rut": negocio_rut,
        "ancho_mm": ancho_mm,
        "autoprint": autoprint,
        "fecha_hora": timezone.localtime(venta.creada_en),
    }

    return render(request, "ventas/ticket.html", context)
