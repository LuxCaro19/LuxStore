from django.db import models

class Producto(models.Model):
    codigo_barras = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Código de barras",
    )

    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre",
    )

    precio = models.PositiveIntegerField(
        verbose_name="Precio",
    )

    stock_actual = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock actual",
    )

    stock_minimo = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock mínimo",
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.codigo_barras:
            self.codigo_barras = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]