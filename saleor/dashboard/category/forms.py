from django import forms
from django.utils.translation import ugettext_lazy as _

from ...product.models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        exclude = []

    def clean_parent(self):
        parent = self.cleaned_data['parent']
        if parent == self.instance:
            raise forms.ValidationError(_('A category may not be made a child of itself'))
        return parent
