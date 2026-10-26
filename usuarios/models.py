from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        VISITA = "VISITA", "Visita"

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="Usuario",
    )
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.VISITA,
        verbose_name="Rol en el sistema",
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Teléfono",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    def __str__(self):
        return f"{self.usuario.username} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN or self.usuario.is_superuser

    @property
    def es_visita(self):
        return self.rol == self.Rol.VISITA and not self.usuario.is_superuser

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuarios"


@receiver(post_save, sender=User)
def asegurar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crea o asegura un perfil para cada usuario registrado.
    Si el usuario es superusuario, su rol por defecto es ADMIN.
    """
    if created:
        rol_inicial = PerfilUsuario.Rol.ADMIN if instance.is_superuser else PerfilUsuario.Rol.VISITA
        PerfilUsuario.objects.get_or_create(usuario=instance, defaults={"rol": rol_inicial})
    else:
        if not hasattr(instance, "perfil"):
            rol_inicial = PerfilUsuario.Rol.ADMIN if instance.is_superuser else PerfilUsuario.Rol.VISITA
            PerfilUsuario.objects.get_or_create(usuario=instance, defaults={"rol": rol_inicial})
