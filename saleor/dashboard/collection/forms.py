from text_unidecode import unidecode

from django import forms
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy

from ...product.models import Collection


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        exclude = ['slug']
        labels = {
            'name': pgettext_lazy(
                'Item name',
                'Name'),
            'products': pgettext_lazy(
                'Products selection',
                'Products')}

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        super(CollectionForm, self).save(commit=commit)
        return self.instance
