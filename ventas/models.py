from django.db import models

from productos.models import Producto


class Venta(models.Model):
    class Estado(models.TextChoices):
        COMPLETADA = "COMPLETADA", "Completada"
        ANULADA = "ANULADA", "Anulada"

    class MedioPago(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TARJETA = "TARJETA", "Tarjeta"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        FIADO = "FIADO", "Fiado"

    total = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Total",
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.COMPLETADA,
        verbose_name="Estado",
    )

    medio_pago = models.CharField(
        max_length=20,
        choices=MedioPago.choices,
        default=MedioPago.EFECTIVO,
        verbose_name="Medio de pago",
    )

    monto_recibido = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Monto recibido",
    )

    creada_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de venta",
    )

    def __str__(self):
        return f"Venta #{self.pk}"

    @property
    def vuelto(self):
        if self.monto_recibido is None:
            return None
        return self.monto_recibido - self.total

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-creada_en"]


class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name="detalles",
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_venta",
    )

    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad",
    )

    precio_unitario = models.PositiveIntegerField(
        verbose_name="Precio unitario",
    )

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"


class CierreCaja(models.Model):
    fecha = models.DateField(
        verbose_name="Fecha del corte",
    )

    cerrado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora de cierre",
    )

    cantidad_ventas = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad de ventas",
    )

    total_efectivo_sistema = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Efectivo según sistema",
    )

    total_tarjeta_sistema = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Tarjeta según sistema",
    )

    total_fiado_sistema = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Fiado según sistema",
    )

    total_vendido = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Total vendido",
    )

    efectivo_real = models.PositiveBigIntegerField(
        verbose_name="Efectivo contado en caja",
    )

    diferencia = models.BigIntegerField(
        default=0,
        verbose_name="Diferencia (Real - Sistema)",
    )

    nota = models.TextField(
        blank=True,
        verbose_name="Nota u observación",
    )

    def __str__(self):
        return f"Cierre de caja {self.fecha} ({self.cerrado_en.strftime('%H:%M')})"

    class Meta:
        verbose_name = "Cierre de caja"
        verbose_name_plural = "Cierres de caja"
        ordering = ["-cerrado_en"]