from __future__ import unicode_literals

from saleor.dashboard.search.forms import ModelFilteredSearchForm
from saleor.order.models import Order
from saleor.product.models import Product
from saleor.userprofile.models import User


def test_model_filtered_search_form_get_models():
    data = {'q': 'test'}
    form = ModelFilteredSearchForm(data)
    assert form.is_valid()
    models = form.get_models()
    assert Order in models
    assert Product in models
    assert User in models

    data = {'q': 'test',
            'models': 'product.product'}
    form = ModelFilteredSearchForm(data)
    assert form.is_valid()
    models = form.get_models()
    assert len(models) == 1
    assert Product in models
