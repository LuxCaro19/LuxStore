import os
import json
from datetime import timedelta
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from productos.models import Producto
from .models import Venta, DetalleVenta, CierreCaja
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.contrib.auth.decorators import login_required
from usuarios.decorators import admin_required
from fiadores.models import Fiador, MovimientoFiado


@login_required
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


@login_required
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


@login_required
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


@login_required
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

    ultimas_ventas = ventas.prefetch_related(
        "detalles__producto",
        "movimientos_fiados__fiador",
    )[:50]

    # Verificar si ya existe un cierre de caja registrado hoy
    ultimo_cierre = CierreCaja.objects.filter(fecha=hoy).order_by("-cerrado_en").first()

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
            "caja_cerrada": ultimo_cierre is not None,
        },
    )


@login_required
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

    if CierreCaja.objects.filter(fecha=hoy).exists():
        return JsonResponse(
            {"ok": False, "mensaje": "La caja de hoy ya fue cerrada previamente."},
            status=400,
        )

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


@admin_required
def historial_ventas(request):
    """
    Módulo de historial de ventas con filtros de fecha, medio de pago y búsqueda,
    además de KPIs dinámicos y visor de boletas térmicas integrado.
    """
    hoy = timezone.localdate()

    q = request.GET.get("q", "").strip()
    periodo = request.GET.get("periodo", "").strip().lower()
    desde_str = request.GET.get("desde", "").strip()
    hasta_str = request.GET.get("hasta", "").strip()
    medio_pago = request.GET.get("medio_pago", "").strip().upper()

    ventas_qs = Venta.objects.filter(estado=Venta.Estado.COMPLETADA)

    # Filtro de búsqueda por ID (#32) o nombre de cliente fiador / producto
    if q:
        q_limpio = q.lstrip("#").strip()
        if q_limpio.isdigit():
            ventas_qs = ventas_qs.filter(id=int(q_limpio))
        else:
            ventas_qs = ventas_qs.filter(
                Q(movimientos_fiados__fiador__nombre__icontains=q)
                | Q(detalles__producto__nombre__icontains=q)
            ).distinct()

    # Filtros de períodos rápidos
    if periodo == "hoy":
        ventas_qs = ventas_qs.filter(creada_en__date=hoy)
        desde_str = hoy.strftime("%Y-%m-%d")
        hasta_str = hoy.strftime("%Y-%m-%d")
    elif periodo == "ayer":
        ayer = hoy - timedelta(days=1)
        ventas_qs = ventas_qs.filter(creada_en__date=ayer)
        desde_str = ayer.strftime("%Y-%m-%d")
        hasta_str = ayer.strftime("%Y-%m-%d")
    elif periodo == "semana":
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        ventas_qs = ventas_qs.filter(creada_en__date__gte=inicio_semana, creada_en__date__lte=hoy)
        desde_str = inicio_semana.strftime("%Y-%m-%d")
        hasta_str = hoy.strftime("%Y-%m-%d")
    elif periodo == "mes":
        inicio_mes = hoy.replace(day=1)
        ventas_qs = ventas_qs.filter(creada_en__date__gte=inicio_mes, creada_en__date__lte=hoy)
        desde_str = inicio_mes.strftime("%Y-%m-%d")
        hasta_str = hoy.strftime("%Y-%m-%d")
    elif periodo == "todo":
        desde_str = ""
        hasta_str = ""
    else:
        # Filtro de rango de fechas personalizado
        if desde_str:
            try:
                desde_fecha = timezone.datetime.strptime(desde_str, "%Y-%m-%d").date()
                ventas_qs = ventas_qs.filter(creada_en__date__gte=desde_fecha)
            except ValueError:
                pass
        if hasta_str:
            try:
                hasta_fecha = timezone.datetime.strptime(hasta_str, "%Y-%m-%d").date()
                ventas_qs = ventas_qs.filter(creada_en__date__lte=hasta_fecha)
            except ValueError:
                pass

    # Filtro por medio de pago
    if medio_pago in dict(Venta.MedioPago.choices):
        ventas_qs = ventas_qs.filter(medio_pago=medio_pago)

    # Métricas agregadas del queryset filtrado
    total_recaudado = ventas_qs.aggregate(total=Sum("total"))["total"] or 0
    cantidad_ventas = ventas_qs.count()
    ticket_promedio = int(total_recaudado / cantidad_ventas) if cantidad_ventas > 0 else 0

    # Orden y prefetch para la visualización paginada
    ventas_ordenadas = ventas_qs.prefetch_related(
        "detalles__producto",
        "movimientos_fiados__fiador",
    ).order_by("-creada_en")

    # Paginación
    paginator = Paginator(ventas_ordenadas, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_recaudado": total_recaudado,
        "cantidad_ventas": cantidad_ventas,
        "ticket_promedio": ticket_promedio,
        "filtros": {
            "q": q,
            "periodo": periodo,
            "desde": desde_str,
            "hasta": hasta_str,
            "medio_pago": medio_pago,
        },
        "medios_pago": Venta.MedioPago.choices,
    }

    return render(request, "ventas/historial.html", context)


@xframe_options_sameorigin
@login_required
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

    from configuracion.models import ConfiguracionNegocio
    cfg = ConfiguracionNegocio.obtener_configuracion()

    negocio_nombre = cfg.nombre_negocio or "LUXSTORE"
    negocio_direccion = cfg.direccion or ""
    negocio_telefono = cfg.telefono or ""
    negocio_rut = cfg.rut or ""
    negocio_giro = cfg.giro or ""
    mensaje_pie = cfg.mensaje_pie_ticket or ""

    ancho_predeterminado = cfg.ancho_papel_predeterminado or "58"
    ancho_mm = request.GET.get("ancho", ancho_predeterminado).strip()
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
        "negocio_giro": negocio_giro,
        "mensaje_pie": mensaje_pie,
        "ancho_mm": ancho_mm,
        "autoprint": autoprint,
        "fecha_hora": timezone.localtime(venta.creada_en),
    }

    return render(request, "ventas/ticket.html", context)
