from django import forms

from ...core.permissions import build_permission_choices
from ...product.models import Product, Category


class PermissionsForm(forms.Form):
    product = forms.MultipleChoiceField(
        label='Products',
        required=False,
        choices=build_permission_choices(cls=Product),
        widget=forms.CheckboxSelectMultiple)
    category = forms.MultipleChoiceField(
        label='Categories',
        required=False,
        choices=build_permission_choices(cls=Category),
        widget=forms.CheckboxSelectMultiple)
