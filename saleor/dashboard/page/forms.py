from django import forms
from django.utils.translation import pgettext_lazy

from ...page.models import Page
from ..product.forms import RichTextField
from ..seo.fields import SeoDescriptionField, SeoTitleField
from ..seo.utils import prepare_seo_description


class PageForm(forms.ModelForm):
    content = RichTextField(
        label=pgettext_lazy('Page form: page content field', 'Content'),
        required=True)

    class Meta:
        model = Page
        exclude = ['created', 'content_json']
        widgets = {
            'slug': forms.TextInput(attrs={'placeholder': 'example-slug'})}
        labels = {
            'title': pgettext_lazy(
                'Page form: title field', 'Title'),
            'slug': pgettext_lazy('Page form: slug field', 'Slug'),
            'available_on': pgettext_lazy(
                'Page form: available on which date field', 'Available on'),
            'is_published': pgettext_lazy(
                'Page form: publication status indicator', 'Is published')}
        help_texts = {
            'slug': pgettext_lazy(
                'Form field help text',
                'Slug is being used to create page URL')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['seo_description'] = SeoDescriptionField(
            extra_attrs={
                'data-bind': self['content'].auto_id,
                'data-materialize': self['content'].html_name})
        self.fields['seo_title'] = SeoTitleField(
            extra_attrs={'data-bind': self['title'].auto_id})

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
