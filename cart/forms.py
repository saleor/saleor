from decimal import Decimal
from django import forms
from django.utils.translation import pgettext as _
from satchless.cart import InvalidQuantityException


class QuantityField(forms.DecimalField):

    pass


class AddToCartForm(forms.Form):

    quantity = QuantityField(_('Form field', 'quantity'), min_value=Decimal(0),
                             max_digits=10, decimal_places=4,
                             initial=Decimal(1))

    def __init__(self, cart, product, *args, **kwargs):
        super(AddToCartForm, self).__init__(*args, **kwargs)
        self.cart = cart
        self.product = product

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        try:
            return self.cart.check_quantity(self.product, quantity)
        except InvalidQuantityException as e:
            raise forms.ValidationError(e.reason)

    def save(self):
        return self.cart.add_item(self.product,
                                  self.cleaned_data['quantity'])

