from django import forms

from ...page.models import Page
from ..product.forms import RichTextField


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        exclude = []

    content = RichTextField()

    def clean_url(self):
        """
        Make sure url is not being written to database with uppercase.
        """
        url = self.cleaned_data.get('url')
        url = url.lower()
        return url
