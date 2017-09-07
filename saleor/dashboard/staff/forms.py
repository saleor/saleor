from django import forms

from ...core.permissions import build_permission_choices
from ...product.models import Product, Category, StockLocation
from ...discount.models import Sale, Voucher
from ...order.models import Order
from ...userprofile.models import User


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
    stock_location = forms.MultipleChoiceField(
        label='Stock Locations',
        required=False,
        choices=build_permission_choices(cls=StockLocation),
        widget=forms.CheckboxSelectMultiple)
    sale = forms.MultipleChoiceField(
        label='Sales',
        required=False,
        choices=build_permission_choices(cls=Sale),
        widget=forms.CheckboxSelectMultiple)
    voucher = forms.MultipleChoiceField(
        label='Vouchers',
        required=False,
        choices=build_permission_choices(cls=Voucher),
        widget=forms.CheckboxSelectMultiple)
    order = forms.MultipleChoiceField(
        label='Orders',
        required=False,
        choices=build_permission_choices(cls=Order),
        widget=forms.CheckboxSelectMultiple)
    user = forms.MultipleChoiceField(
        label='Users',
        required=False,
        choices=build_permission_choices(cls=User),
        widget=forms.CheckboxSelectMultiple)
