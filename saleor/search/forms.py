from django import forms
from django.utils.translation import pgettext

from .backends import picker


class SearchForm(forms.Form):
    q = forms.CharField(
        label=pgettext('Search form label', 'Query'), required=True)

    def search(self):
        search = picker.pick_backend()
        return search(self.cleaned_data['q'])
