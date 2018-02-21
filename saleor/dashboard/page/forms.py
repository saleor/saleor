from django import forms
from django.forms import inlineformset_factory

from ...page.models import Page, PostAsset
from ..product.forms import RichTextField


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        exclude = []

    content = RichTextField()

AssetUploadFormset = inlineformset_factory(
    Page, PostAsset, fields=['page', 'asset'], extra=3)
