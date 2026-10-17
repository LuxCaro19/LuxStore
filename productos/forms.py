from django import forms

from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto

        fields = [
            "nombre",
            "codigo_barras",
            "precio_compra",
            "porcentaje_ganancia",
            "precio",
            "stock_actual",
            "stock_minimo",
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control lux-input product-name-input",
                    "placeholder": "NOMBRE DEL PRODUCTO",
                    "autocomplete": "off",
                    "autofocus": True,
                }
            ),
            "codigo_barras": forms.TextInput(
                attrs={
                    "class": "form-control lux-input",
                    "placeholder": "Escanea o ingresa el código",
                    "autocomplete": "off",
                }
            ),
            "precio_compra": forms.NumberInput(
                attrs={
                    "class": "form-control lux-input",
                    "placeholder": "0",
                    "min": "0",
                }
            ),
            "porcentaje_ganancia": forms.NumberInput(
                attrs={
                    "class": "form-control lux-input",
                    "placeholder": "0",
                    "min": "0",
                    "step": "0.01",
                }
            ),
            "precio": forms.NumberInput(
                attrs={
                    "class": "form-control lux-input",
                    "placeholder": "0",
                    "min": "0",
                }
            ),
            "stock_actual": forms.NumberInput(
                attrs={
                    "class": "form-control lux-input",
                    "placeholder": "0",
                    "min": "0",
                }
            ),
            "stock_minimo": forms.NumberInput(
                attrs={
                    "class": "form-control lux-input",
                    "placeholder": "0",
                    "min": "0",
                }
            ),
            "activo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }