from django.db import models

from productos.models import Producto


class Venta(models.Model):
    class Estado(models.TextChoices):
        COMPLETADA = "COMPLETADA", "Completada"
        ANULADA = "ANULADA", "Anulada"

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

    creada_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de venta",
    )

    def __str__(self):
        return f"Venta #{self.pk}"

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