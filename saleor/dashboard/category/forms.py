from django import forms
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from text_unidecode import unidecode

from ...product.models import Category


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.parent_pk = kwargs.pop('parent_pk')
        super().__init__(*args, **kwargs)
        field_maxlength = self.fields['seo_description'].max_length
        # Placeholder should be no longer than fields maximum size
        placeholder = self.instance.description[:field_maxlength]
        self.fields['seo_description'].widget.attrs.update({
            'id': 'seo_description',
            'data-bind': self['description'].auto_id,
            'placeholder': placeholder})
        self.fields['seo_title'].widget.attrs.update({
            'id': 'seo_title',
            'data-bind': self['name'].auto_id,
            'placeholder': self.instance.name})

    class Meta:
        model = Category
        exclude = ['slug']
        labels = {
            'name': pgettext_lazy(
                'Item name',
                'Name'),
            'description': pgettext_lazy(
                'Description',
                'Description')}

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        if self.parent_pk:
            self.instance.parent = get_object_or_404(
                Category, pk=self.parent_pk)
        return super().save(commit=commit)
