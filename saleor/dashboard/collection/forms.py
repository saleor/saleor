from unidecode import unidecode

from django import forms
from django.utils.text import slugify

from ...product.models import Collection


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        exclude = ['slug']

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        super(CollectionForm, self).save(commit=commit)
        return self.instance
