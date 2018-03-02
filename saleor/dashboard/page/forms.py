from django import forms

from ...page.models import Page
from ..product.forms import RichTextField


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        exclude = []
        widgets = {
            'slug': forms.TextInput(attrs={'placeholder': 'example-slug'})}

    content = RichTextField()

    def clean_slug(self):
        # Make sure slug is not being written to database with uppercase.
        slug = self.cleaned_data.get('slug')
        slug = slug.lower()
        return slug

