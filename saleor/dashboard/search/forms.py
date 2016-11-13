from django import forms
from django.template.defaultfilters import capfirst
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from haystack.forms import SearchForm
from haystack.utils import get_model_ct
from haystack.utils.app_loading import haystack_get_model

from ...order.models import Order
from ...product.models import Product
from ...userprofile.models import User


class ModelFilteredSearchForm(SearchForm):
    MODELS_EMPTY_LABEL = _('All models')
    INDEXED_MODELS = [Order, User, Product]

    def __init__(self, *args, **kwargs):
        super(ModelFilteredSearchForm, self).__init__(*args, **kwargs)
        self.fields['models'] = forms.ChoiceField(
            choices=self.model_choices(), required=False, label=_('Search In'),
            widget=forms.Select)

    def model_choices(self):
        choices = [(get_model_ct(m),
                    capfirst(smart_text(m._meta.verbose_name_plural)))
                   for m in self.INDEXED_MODELS]
        choices.insert(0, (None, self.MODELS_EMPTY_LABEL))
        return sorted(choices, key=lambda x: x[1])

    def get_models(self):
        if self.is_valid() and self.cleaned_data['models']:
            model_name = self.cleaned_data['models'].split('.')
            search_models = [haystack_get_model(*model_name)]
        else:
            search_models = self.INDEXED_MODELS
        return search_models

    def search(self):
        sqs = super(ModelFilteredSearchForm, self).search()
        return sqs.models(*self.get_models())
