from . import InsufficientStockException
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
    error_messages = {
        'insufficient-stock': _('Only %(remaining)d remaining in stock.')}

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        self.product = kwargs.pop('product')
        self.cart_line = self.cart.get_line(self.product)

        super(AddToCartForm, self).__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.cart_line:
            new_quantity = quantity + self.cart_line.quantity
        else:
            new_quantity = quantity
        try:
            self.cart.check_quantity(self.product, new_quantity)
        except InsufficientStockException as e:
            remaining = e.product.stock - quantity
            msg = self.error_messages['insufficient-stock']
            raise forms.ValidationError(msg % {'remaining': remaining})
        return quantity

    def save(self):
        return self.cart.add(self.product, self.cleaned_data['quantity'])


class ReplaceCartLineForm(AddToCartForm):

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        try:
            self.cart.check_quantity(self.product, quantity)
        except InsufficientStockException as e:
            msg = self.error_messages['insufficient-stock']
            raise forms.ValidationError(msg % {'remaining': e.product.stock})
        return quantity

    def save(self):
        return self.cart.add(self.product, self.cleaned_data['quantity'],
                             replace=True)


class ReplaceCartLineFormSet(BaseFormSet):

    form = ReplaceCartLineForm
    extra = 0
    can_order = False,
    can_delete = False
    max_num = None

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        kwargs['initial'] = [{'quantity':cart_line.get_quantity()}
						     for cart_line in self.cart
                             if cart_line.get_quantity()]

        super(ReplaceCartLineFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['cart'] = self.cart
        kwargs['product'] = self.cart[i].product
        return super(ReplaceCartLineFormSet, self)._construct_form(i, **kwargs)

    def save(self):
        for form in self.forms:
            form.save()
