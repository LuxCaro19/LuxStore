from django.db import models
from django.db.models import Sum


class Fiador(models.Model):
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre",
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.nombre

    @property
    def saldo(self):
        cargos = (
            self.movimientos
            .filter(tipo=MovimientoFiado.Tipo.CARGO)
            .aggregate(total=Sum("monto"))["total"]
            or 0
        )

        abonos = (
            self.movimientos
            .filter(tipo=MovimientoFiado.Tipo.ABONO)
            .aggregate(total=Sum("monto"))["total"]
            or 0
        )

        return cargos - abonos

    class Meta:
        verbose_name = "Fiador"
        verbose_name_plural = "Fiadores"
        ordering = ["nombre"]


class MovimientoFiado(models.Model):
    class Tipo(models.TextChoices):
        CARGO = "CARGO", "Cargo"
        ABONO = "ABONO", "Abono"

    fiador = models.ForeignKey(
        Fiador,
        on_delete=models.PROTECT,
        related_name="movimientos",
    )

    venta = models.ForeignKey(
        "ventas.Venta",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_fiados",
    )

    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
    )

    monto = models.PositiveBigIntegerField()

    nota = models.CharField(
        max_length=250,
        blank=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.fiador} - {self.tipo} - ${self.monto}"

    class Meta:
        verbose_name = "Movimiento fiado"
        verbose_name_plural = "Movimientos fiados"
        ordering = ["-creado_en"]