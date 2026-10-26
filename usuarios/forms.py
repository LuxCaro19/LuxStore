from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import PerfilUsuario


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "class": "form-control lux-input",
                "placeholder": "Ingresa tu nombre de usuario",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control lux-input",
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        ),
    )


class UsuarioCrearForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombre completo / Descriptivo",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control lux-input",
                "placeholder": "Ej: Juan Pérez o Cajero Tarde",
            }
        ),
    )
    username = forms.CharField(
        label="Nombre de usuario (Login)",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control lux-input",
                "placeholder": "Ej: visita, cajero1",
                "autocomplete": "off",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control lux-input",
                "placeholder": "Ingresa una contraseña segura",
                "autocomplete": "new-password",
            }
        ),
    )
    rol = forms.ChoiceField(
        label="Rol en el sistema",
        choices=PerfilUsuario.Rol.choices,
        initial=PerfilUsuario.Rol.VISITA,
        widget=forms.Select(attrs={"class": "form-select lux-select"}),
        help_text="Visita: Solo accede a Punto de Venta y Corte Diario. Admin: Acceso total.",
    )

    class Meta:
        model = User
        fields = ["first_name", "username", "password"]

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
            perfil.rol = self.cleaned_data.get("rol", PerfilUsuario.Rol.VISITA)
            perfil.save()
        return user


class UsuarioEditarForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombre completo / Descriptivo",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control lux-input",
                "placeholder": "Ej: Juan Pérez o Cajero Tarde",
                "autocomplete": "off",
            }
        ),
    )
    rol = forms.ChoiceField(
        label="Rol en el sistema",
        choices=PerfilUsuario.Rol.choices,
        widget=forms.Select(attrs={"class": "form-select lux-select"}),
    )
    is_active = forms.BooleanField(
        label="Usuario activo",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "role": "switch",
            }
        ),
    )
    nueva_password = forms.CharField(
        label="Nueva contraseña (dejar en blanco para no cambiarla)",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control lux-input",
                "placeholder": "••••••••",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["first_name", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, "perfil"):
            self.fields["rol"].initial = self.instance.perfil.rol

    def save(self, commit=True):
        user = super().save(commit=False)
        nueva_pass = self.cleaned_data.get("nueva_password")
        if nueva_pass:
            user.set_password(nueva_pass)
        if commit:
            user.save()
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
            perfil.rol = self.cleaned_data.get("rol", PerfilUsuario.Rol.VISITA)
            perfil.save()
        return user
