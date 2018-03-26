from django import forms
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from text_unidecode import unidecode

from ...core.utils import merge_dicts
from ...product.models import Category
from ..seo.utils import (
    MIN_DESCRIPTION_LENGTH, MIN_TITLE_LENGTH, SEO_HELP_TEXTS, SEO_LABELS,
    SEO_WIDGETS)


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.parent_pk = kwargs.pop('parent_pk')
        super().__init__(*args, **kwargs)
        self.fields['seo_description'].widget.attrs.update({
            'data-bind': self['description'].auto_id,
            'min-recommended-length': MIN_DESCRIPTION_LENGTH})
        self.fields['seo_title'].widget.attrs.update({
            'data-bind': self['name'].auto_id,
            'min-recommended-length': MIN_TITLE_LENGTH})

    class Meta:
        model = Category
        exclude = ['slug']
        labels = merge_dicts(
            {
                'name': pgettext_lazy('Item name', 'Name'),
                'description': pgettext_lazy('Description', 'Description')
            },
            SEO_LABELS)
        help_texts = SEO_HELP_TEXTS
        widgets = SEO_WIDGETS

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        if self.parent_pk:
            self.instance.parent = get_object_or_404(
                Category, pk=self.parent_pk)
        return super().save(commit=commit)
