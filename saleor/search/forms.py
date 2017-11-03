from django import forms
from django.utils.translation import pgettext
from .backends import newelastic


class SearchForm(forms.Form):
    q = forms.CharField(
        label=pgettext('Search form label', 'Query'), required=True)

    def search(self, model_or_queryset):
        query = self.cleaned_data['q']
        results = newelastic.SearchBackend.search(
            query, model_or_queryset=model_or_queryset)
        return results
