from django.db.models import F, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from usuarios.decorators import admin_required

from .forms import ProductoForm
from .models import Producto


@admin_required
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


@admin_required
def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)

        if form.is_valid():
            producto = form.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "ok": True,
                        "mensaje": "Producto creado con éxito",
                        "redirect_url": reverse("productos:lista"),
                        "producto": {
                            "id": producto.id,
                            "nombre": producto.nombre,
                        },
                    }
                )

            return redirect("productos:lista")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            errores = {
                campo: [error["message"] for error in lista]
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
        form = ProductoForm()

    return render(
        request,
        "productos/crear.html",
        {
            "form": form,
        },
    )


@admin_required
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


@admin_required
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


@admin_required
def ajustar_stock(request, pk):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    producto = get_object_or_404(Producto, pk=pk)

    try:
        cantidad = int(request.POST.get("cantidad", 0))
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "Cantidad inválida"}, status=400)

    nuevo_stock = producto.stock_actual + cantidad
    if nuevo_stock < 0:
        return JsonResponse({"ok": False, "error": "El stock no puede quedar en negativo"}, status=400)

    producto.stock_actual = nuevo_stock
    producto.save(update_fields=["stock_actual"])

    if producto.stock_actual == 0:
        estado = "empty"
        estado_label = "Sin stock"
    elif producto.stock_actual <= producto.stock_minimo:
        estado = "low"
        estado_label = "Stock bajo"
    else:
        estado = "ok"
        estado_label = "Disponible"

    return JsonResponse({
        "ok": True,
        "producto_id": producto.id,
        "stock_actual": producto.stock_actual,
        "stock_minimo": producto.stock_minimo,
        "estado": estado,
        "estado_label": estado_label,
        "mensaje": f"Stock actualizado a {producto.stock_actual} unid.",
    })


@admin_required
def exportar_inventario_excel(request):
    """
    Genera y descarga un archivo Excel (.xlsx) con el inventario completo,
    precios, márgenes, existencias y valorización total del stock.
    """
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    productos = Producto.objects.filter(activo=True).order_by("nombre")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventario"
    ws.views.sheetView[0].showGridLines = True

    font_titulo = Font(name="Segoe UI", size=13, bold=True, color="1E293B")
    font_sub = Font(name="Segoe UI", size=9, italic=True, color="64748B")
    font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    font_row = Font(name="Segoe UI", size=10, color="0F172A")
    font_bold = Font(name="Segoe UI", size=10, bold=True, color="0F172A")

    fill_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    fill_total = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    fill_alt = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )
    double_bottom_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="double", color="0F172A"),
    )

    ws["A1"] = "LuxStore - Inventario Valorizado de Productos"
    ws["A1"].font = font_titulo
    ws["A2"] = f"Generado el: {timezone.localtime().strftime('%d/%m/%Y %H:%M')} | Total productos activos: {productos.count()}"
    ws["A2"].font = font_sub

    headers = [
        "ID", "Código de Barras", "Producto", "Precio Compra ($)",
        "Margen (%)", "Precio Venta ($)", "Stock Actual", "Stock Mínimo",
        "Estado", "Valorización Stock ($)"
    ]

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center" if col_idx in [1, 2, 7, 8, 9] else ("right" if col_idx in [4, 5, 6, 10] else "left"))
        cell.border = thin_border

    row_idx = 5
    for p in productos:
        if p.stock_actual == 0:
            estado_str = "Agotado"
        elif p.stock_actual <= p.stock_minimo:
            estado_str = "Stock bajo"
        else:
            estado_str = "Disponible"

        row_data = [
            p.id,
            p.codigo_barras or "-",
            p.nombre,
            p.precio_compra or 0,
            float(p.porcentaje_ganancia or 0) / 100,
            p.precio,
            p.stock_actual,
            p.stock_minimo,
            estado_str,
            f"=F{row_idx}*G{row_idx}",
        ]

        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_row
            cell.border = thin_border
            if row_idx % 2 == 0:
                cell.fill = fill_alt

            if col_idx in [1, 2, 9]:
                cell.alignment = Alignment(horizontal="center")
            elif col_idx in [7, 8]:
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="center")
            elif col_idx == 5:
                cell.number_format = '0.0%'
                cell.alignment = Alignment(horizontal="right")
            elif col_idx in [4, 6, 10]:
                cell.number_format = '"$"#,##0'
                cell.alignment = Alignment(horizontal="right")

        row_idx += 1

    if row_idx > 5:
        total_label = ws.cell(row=row_idx, column=6, value="TOTALES:")
        total_label.font = font_bold
        total_label.alignment = Alignment(horizontal="right")
        total_label.border = double_bottom_border
        total_label.fill = fill_total

        total_stock = ws.cell(row=row_idx, column=7, value=f"=SUM(G5:G{row_idx-1})")
        total_stock.font = font_bold
        total_stock.number_format = '#,##0'
        total_stock.alignment = Alignment(horizontal="center")
        total_stock.border = double_bottom_border
        total_stock.fill = fill_total

        for c in [8, 9]:
            cell_blank = ws.cell(row=row_idx, column=c)
            cell_blank.border = double_bottom_border
            cell_blank.fill = fill_total

        total_val = ws.cell(row=row_idx, column=10, value=f"=SUM(J5:J{row_idx-1})")
        total_val.font = font_bold
        total_val.number_format = '"$"#,##0'
        total_val.alignment = Alignment(horizontal="right")
        total_val.border = double_bottom_border
        total_val.fill = fill_total

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"LuxStore_Inventario_{timezone.localdate().strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
