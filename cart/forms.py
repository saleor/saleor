from . import InvalidQuantityException
from decimal import Decimal
from django import forms
from django.forms.formsets import BaseFormSet
from django.utils.translation import pgettext as _


class QuantityField(forms.DecimalField):

    pass


class AddToCartForm(forms.Form):

    quantity = QuantityField(_('Form field', 'quantity'), min_value=Decimal(0),
                             max_digits=10, decimal_places=4,
                             initial=Decimal(1))

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        self.product = kwargs.pop('product')
        self.cart_line = self.cart.get_line(self.product)

        super(AddToCartForm, self).__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']

        try:
            self.cart.check_quantity(self.product,
                quantity + self.cart_line.quantity if
                self.cart_line else quantity)
        except InvalidQuantityException as e:
            raise forms.ValidationError(e)

        return quantity

    def save(self):
        return self.cart.add_line(self.product,
                                  self.cleaned_data['quantity'])


class ReplaceCartLineForm(AddToCartForm):

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']

        try:
            self.cart.check_quantity(self.product, quantity)
        except InvalidQuantityException as e:
            raise forms.ValidationError(e)

        return quantity

    def save(self):
        return self.cart.add_line(self.product,
                                  self.cleaned_data['quantity'], replace=True)


class ReplaceCartLineFormSet(BaseFormSet):

    form = ReplaceCartLineForm
    extra = 0
    can_order = False,
    can_delete = False
    max_num = None

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        kwargs['initial'] = [{'quantity':cart_line.get_quantity()} for
                             cart_line in self.cart]

        super(ReplaceCartLineFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['cart'] = self.cart
        kwargs['product'] = self.cart[i].product
        return super(ReplaceCartLineFormSet, self)._construct_form(i, **kwargs)

    def save(self):
        for form in self.forms:
            form.save()
