from django import forms
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from text_unidecode import unidecode

from ...product.models import Collection, Product
from ..forms import AjaxSelect2MultipleChoiceField


class CollectionForm(forms.ModelForm):
    products = AjaxSelect2MultipleChoiceField(
        queryset=Product.objects.all(),
        fetch_data_url=reverse_lazy('dashboard:ajax-products'), required=False)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['products'].set_initial(self.instance.products.all())

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        super().save(commit=commit)
        return self.instance
