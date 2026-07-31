from django import forms
from .models import Product, Category


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            "category",
            "name",
            "price",
            "description",
            "stock",
            "image",
        ]

        widgets = {

            "category": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Product Name"
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Price"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Enter Product Description"
                }
            ),

            "stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Stock Quantity",
                    "min": 0
                }
            ),

            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control"
                }
            ),
        }


class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category

        fields = [
            "name",
            "image",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Category Name"
                }
            ),

            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control"
                }
            ),
        }