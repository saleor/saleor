from django import forms
from django.utils.translation import pgettext
from .backends import elasticsearch


class SearchForm(forms.Form):
    q = forms.CharField(
        label=pgettext('Search form label', 'Query'), required=True)

    def search(self):
        return elasticsearch.search(self.cleaned_data['q'])
