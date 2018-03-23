from django import forms
from django.utils.translation import pgettext_lazy

from ...core.utils.text import generate_seo_description
from ...page.models import Page
from ..product.forms import RichTextField
from ..seo.utils import SEO_HELP_TEXTS, SEO_LABELS


class PageForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Placeholder should be no longer than fields maximum size
        field_maxlength = self.fields['seo_description'].max_length
        # Page's content contains htm tags which should be stripped
        placeholder = generate_seo_description(
            self.instance.content, field_maxlength)
        self.fields['seo_description'].widget.attrs.update({
            'id': 'seo_description',
            'data-bind': self['content'].auto_id,
            'data-materialize': self['content'].html_name,
            'placeholder': placeholder})
        self.fields['seo_title'].widget.attrs.update({
            'id': 'seo_title',
            'data-bind': self['title'].auto_id,
            'placeholder': self.instance.title})

    class Meta:
        model = Page
        exclude = []
        widgets = {
            'slug': forms.TextInput(attrs={'placeholder': 'example-slug'})}
        labels = {
            'is_visible': pgettext_lazy(
                'Visibility status indicator', 'Publish'),
            **SEO_LABELS}
        help_texts = {
            'slug': pgettext_lazy(
                'Form field help text',
                'Slug is being used to create page URL'),
            **SEO_HELP_TEXTS}

    content = RichTextField()

    def clean_slug(self):
        # Make sure slug is not being written to database with uppercase.
        slug = self.cleaned_data.get('slug')
        slug = slug.lower()
        return slug

    def clean_seo_description(self):
        seo_description = self.cleaned_data['seo_description']

        # if there is no SEO friendly description set,
        # generate it from the HTML description
        if not seo_description:
            # get the non-safe description (has non escaped HTML tags in it)
            description = self.data['description']

            # generate a SEO friendly from HTML description
            seo_description = generate_seo_description(description, 300)
        return seo_description
