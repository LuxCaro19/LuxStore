from django import forms
from .models import ConfiguracionNegocio


class ConfiguracionNegocioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionNegocio
        fields = [
            "nombre_negocio",
            "rut",
            "giro",
            "direccion",
            "telefono",
            "mensaje_pie_ticket",
            "ancho_papel_predeterminado",
        ]
        widgets = {
            "nombre_negocio": forms.TextInput(
                attrs={"class": "form-control lux-input", "placeholder": "Ej: Minimarket LuxStore", "required": True}
            ),
            "rut": forms.TextInput(
                attrs={"class": "form-control lux-input", "placeholder": "Ej: 76.123.456-7"}
            ),
            "giro": forms.TextInput(
                attrs={"class": "form-control lux-input", "placeholder": "Ej: Minimarket y rotisería"}
            ),
            "direccion": forms.TextInput(
                attrs={"class": "form-control lux-input", "placeholder": "Ej: Av. Los Aromos #450"}
            ),
            "telefono": forms.TextInput(
                attrs={"class": "form-control lux-input", "placeholder": "Ej: +56 9 8765 4321"}
            ),
            "mensaje_pie_ticket": forms.Textarea(
                attrs={
                    "class": "form-control lux-input",
                    "rows": 3,
                    "placeholder": "Ej: ¡Gracias por su compra!\nCambio de productos con boleta.",
                }
            ),
            "ancho_papel_predeterminado": forms.Select(
                attrs={"class": "form-select lux-select"}
            ),
        }
