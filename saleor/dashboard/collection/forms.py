from django import forms
from ...product.models import Collection


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        exclude = []
