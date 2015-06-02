from django import forms

from ...product.models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        exclude = []