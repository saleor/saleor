from django import forms
from django.utils.translation import ugettext_lazy as _
from mptt.forms import TreeNodeChoiceField

from ...product.models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        exclude = []

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.fields['parent'] = TreeNodeChoiceField(queryset=Category.objects.all())

    def clean_parent(self):
        parent = self.cleaned_data['parent']
        if parent == self.instance:
            raise forms.ValidationError(_('A category may not be made a child of itself'))
        if self.instance in parent.get_ancestors():
            raise forms.ValidationError(_('A category may not be made a child of any of its descendants.'))
        return parent
