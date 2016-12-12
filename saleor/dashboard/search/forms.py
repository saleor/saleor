from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from ...order.models import Order
from ...product.models import Product
from ...search.forms import SearchForm
from ...userprofile.models import User


class ModelFilteredSearchForm(SearchForm):
    MODELS_EMPTY_LABEL = _('All')
    MODEL_MAPPING = {
        'Orders': Order,
        'Users': User,
        'Products': Product}
    search_in = forms.ChoiceField(choices=(
        (label, label) for label in MODEL_MAPPING
    ), widget=forms.Select)

    def get_model(self):
        if self.is_valid() and self.cleaned_data['models']:
            model_name = self.cleaned_data['models']
            return self.MODEL_MAPPING[model_name]
        return Order

    def search(self):
        return super(ModelFilteredSearchForm, self).search(
            model_or_queryset=self.get_model())
