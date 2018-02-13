from django import forms
from django.forms import inlineformset_factory

from ...page.models import Page, PostAsset
from ..widgets import AceWidget


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        exclude = []
        widgets = {
            'head_tags': AceWidget(mode=AceWidget.HTML),
            'content': AceWidget(mode=AceWidget.HTML),
            'javascript': AceWidget(mode=AceWidget.JS)
        }


AssetUploadFormset = inlineformset_factory(
    Page, PostAsset, fields=['page', 'asset'], extra=3)
