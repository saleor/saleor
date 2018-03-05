from django import forms
from django.utils.translation import pgettext_lazy

from ...page.models import Page
from ..product.forms import RichTextField


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        exclude = []
        widgets = {
            'slug': forms.TextInput(attrs={'placeholder': 'example-slug'})}
        labels = {
            'is_visible': pgettext_lazy(
                'Visibility status indicator', 'Publish')}
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
