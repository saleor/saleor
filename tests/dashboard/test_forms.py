from django import forms

from saleor.product.models import Category
from saleor.dashboard.product.forms import ModelChoiceOrCreationField


def test_model_choice_or_creation_field(default_category):
    class Form(forms.Form):
        field = ModelChoiceOrCreationField(queryset=Category.objects.all())

    form = Form({'field': default_category})
    assert form.is_valid()
    assert form.cleaned_data['field'] == default_category

    choice = 'new-value'
    form = Form({'field': choice})
    assert form.is_valid()
    assert form.cleaned_data['field'] == choice
