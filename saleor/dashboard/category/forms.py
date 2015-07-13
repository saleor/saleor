from django import forms
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from mptt.forms import TreeNodeChoiceField
from unidecode import unidecode

from ...product.models import Category


class CategoryForm(forms.ModelForm):
    parent = TreeNodeChoiceField(queryset=Category.objects.all(),
                                 required=False)

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        if self.instance.parent and self.instance.parent.hidden:
            self.fields['hidden'].widget.attrs['disabled'] = True

    class Meta:
        model = Category
        exclude = ['slug']

    def clean_parent(self):
        parent = self.cleaned_data['parent']
        if parent:
            if parent == self.instance:
                raise forms.ValidationError(_('A category may not be made a child of itself'))
            if self.instance in parent.get_ancestors():
                raise forms.ValidationError(_('A category may not be made a child of any of its descendants.'))
        return parent

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        if self.instance.parent and self.instance.parent.hidden:
            self.instance.hidden = True
        super(CategoryForm, self).save(commit=commit)
        self.instance.set_hidden_descendants(self.cleaned_data['hidden'])
        return self.instance
