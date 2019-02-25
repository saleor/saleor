from django import forms
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from text_unidecode import unidecode

from ...product.models import Collection, Product
from ...product.thumbnails import create_collection_background_image_thumbnails
from ...site.models import SiteSettings
from ..forms import AjaxSelect2MultipleChoiceField
from ..seo.fields import SeoDescriptionField, SeoTitleField


class CollectionForm(forms.ModelForm):
    products = AjaxSelect2MultipleChoiceField(
        queryset=Product.objects.all(),
        fetch_data_url=reverse_lazy('dashboard:ajax-products'), required=False,
        label=pgettext_lazy('Products selection', 'Products'))

    class Meta:
        model = Collection
        exclude = ['slug', 'description_json']
        labels = {
            'name': pgettext_lazy('Item name', 'Name'),
            'background_image': pgettext_lazy(
                'Background image of a collection',
                'Background image'),
            'background_image_alt': pgettext_lazy(
                'Description of a collection image', 'Image description'),
            'is_published': pgettext_lazy(
                'Collection published toggle',
                'Published'),
            'publication_date': pgettext_lazy(
                'The publication date field, can be a posterior date for '
                'a planned publication.',
                'Publication date'),
            'description': pgettext_lazy(
                'Description field of a collection',
                'Description')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['products'].set_initial(self.instance.products.all())
        self.fields['seo_description'] = SeoDescriptionField(
            extra_attrs={'data-bind': self['description'].auto_id})
        self.fields['seo_title'] = SeoTitleField(
            extra_attrs={'data-bind': self['name'].auto_id})

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        instance = super().save(commit=commit)

        if instance.pk and 'background_image' in self.changed_data:
            create_collection_background_image_thumbnails.delay(instance.pk)

        return instance


class AssignHomepageCollectionForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ('homepage_collection',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['homepage_collection'].queryset = \
            Collection.objects.filter(is_published=True)
