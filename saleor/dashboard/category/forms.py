from __future__ import unicode_literals

from django import forms
from django.shortcuts import get_object_or_404
from django.utils.translation import pgettext_lazy
from django.utils.text import slugify
from text_unidecode import unidecode

from ...product.models import Category


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.parent_pk = kwargs.pop('parent_pk')
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.fields['is_hidden'].label = pgettext_lazy(
            'Category form field label', 'Hide in site navigation')
        if self.instance.parent and self.instance.parent.is_hidden:
            self.fields['is_hidden'].widget.attrs['disabled'] = True

    class Meta:
        model = Category
        exclude = ['slug']

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        if self.parent_pk:
            self.instance.parent = get_object_or_404(
                Category, pk=self.parent_pk)
        if self.instance.parent and self.instance.parent.is_hidden:
            self.instance.is_hidden = True
        super(CategoryForm, self).save(commit=commit)
        self.instance.set_is_hidden_descendants(self.cleaned_data['is_hidden'])
        return self.instance
