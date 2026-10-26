from django.db import models


class ConfiguracionNegocio(models.Model):
    class AnchoPapel(models.TextChoices):
        MM58 = "58", "58 mm (Rollo angosto)"
        MM80 = "80", "80 mm (Rollo ancho)"

    nombre_negocio = models.CharField(
        max_length=100,
        default="LUXSTORE",
        verbose_name="Nombre comercial del negocio",
    )
    rut = models.CharField(
        max_length=20,
        blank=True,
        default="76.123.456-7",
        verbose_name="RUT / Identificación tributaria",
    )
    giro = models.CharField(
        max_length=150,
        blank=True,
        default="Comercio al por menor",
        verbose_name="Giro o actividad comercial",
    )
    direccion = models.CharField(
        max_length=200,
        blank=True,
        default="Calle Principal #123",
        verbose_name="Dirección física",
    )
    telefono = models.CharField(
        max_length=50,
        blank=True,
        default="+56 9 1234 5678",
        verbose_name="Teléfono / WhatsApp de contacto",
    )
    mensaje_pie_ticket = models.TextField(
        blank=True,
        default="¡Gracias por su preferencia!\nCambio de productos con boleta.",
        verbose_name="Mensaje de pie de boleta / ticket",
    )
    ancho_papel_predeterminado = models.CharField(
        max_length=10,
        choices=AnchoPapel.choices,
        default=AnchoPapel.MM58,
        verbose_name="Ancho de papel predeterminado",
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    @classmethod
    def obtener_configuracion(cls):
        """
        Retorna la única instancia de configuración, creándola si no existe.
        """
        config, _ = cls.objects.get_or_create(id=1)
        return config

    def __str__(self):
        return f"Configuración: {self.nombre_negocio}"

    class Meta:
        verbose_name = "Configuración del negocio"
        verbose_name_plural = "Configuración del negocio"
