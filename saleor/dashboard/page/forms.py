from django import forms
from django.utils.translation import pgettext_lazy

from ...page.models import Page
from ..product.forms import RichTextField
from ..seo.fields import SeoDescriptionField, SeoTitleField
from ..seo.utils import prepare_seo_description


class PageForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['seo_description'] = SeoDescriptionField(
            extra_attrs={
                'data-bind': self['content'].auto_id,
                'data-materialize': self['content'].html_name})
        self.fields['seo_title'] = SeoTitleField(
            extra_attrs={'data-bind': self['title'].auto_id})

    class Meta:
        model = Page
        exclude = []
        widgets = {
            'slug': forms.TextInput(attrs={'placeholder': 'example-slug'})},
        labels = {
            'is_visible': pgettext_lazy(
                'Visibility status indicator', 'Publish')},
        help_texts = {
            'slug': pgettext_lazy(
                'Form field help text',
                'Slug is being used to create page URL')}

    content = RichTextField()

    def clean_slug(self):
        # Make sure slug is not being written to database with uppercase.
        slug = self.cleaned_data.get('slug')
        slug = slug.lower()
        return slug

    def clean_seo_description(self):
        seo_description = prepare_seo_description(
            seo_description=self.cleaned_data['seo_description'],
            html_description=self.data['content'],
            max_length=self.fields['seo_description'].max_length)
        return seo_description
