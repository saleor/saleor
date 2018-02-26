from django import forms
from django.forms import inlineformset_factory

from ...page.models import Page
from ..product.forms import RichTextField


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        exclude = []

    content = RichTextField()
