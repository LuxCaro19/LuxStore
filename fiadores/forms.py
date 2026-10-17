from django import forms

from .models import Fiador


class FiadorForm(forms.ModelForm):
    class Meta:
        model = Fiador

        fields = [
            "nombre",
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control lux-input",
                    "placeholder": "Nombre del fiador",
                    "autocomplete": "off",
                    "autofocus": True,
                }
            ),

            "activo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }