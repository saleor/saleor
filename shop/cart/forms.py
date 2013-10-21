from decimal import Decimal

from django import forms
from django.forms.formsets import BaseFormSet
from django.utils.translation import pgettext, ugettext
from satchless.item import InsufficientStock


class QuantityField(forms.DecimalField):

    def __init__(self, *args, **kwargs):
        super(QuantityField, self).__init__(
            *args, max_value=None, min_value=Decimal(0), max_digits=10,
            decimal_places=4, initial=Decimal(1), **kwargs)


class AddToCartForm(forms.Form):
    '''
    Class use product and cart instance.
    '''
    quantity = QuantityField(label=pgettext('Form field', 'Quantity'))
    error_messages = {
        'empty-stock': ugettext(
            'Out of stock.'),
        'insufficient-stock': ugettext(
            'Only %(remaining)d remaining in stock.')}

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        self.product = kwargs.pop('product')
        self.cart_line = self.cart.get_line(self.product)
        super(AddToCartForm, self).__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        used_quantity = self.cart_line.quantity if self.cart_line else 0
        new_quantity = quantity + used_quantity
        try:
            self.cart.check_quantity(self.product, new_quantity, None)
        except InsufficientStock as e:
            remaining = e.item.stock - used_quantity
            if remaining:
                msg = self.error_messages['insufficient-stock']
            else:
                msg = self.error_messages['empty-stock']
            raise forms.ValidationError(msg % {'remaining': remaining})
        return quantity

    def save(self):
        '''
        Adds CartLine into the Cart instance.
        '''
        return self.cart.add(self.product, self.cleaned_data['quantity'])


class ReplaceCartLineForm(AddToCartForm):
    '''
    Replaces quantity in CartLine.
    '''
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        try:
            self.cart.check_quantity(self.product, quantity, None)
        except InsufficientStock as e:
            msg = self.error_messages['insufficient-stock']
            raise forms.ValidationError(msg % {'remaining': e.item.stock})
        return quantity

    def save(self):
        '''
        Replace quantity.
        '''
        return self.cart.add(self.product, self.cleaned_data['quantity'],
                             replace=True)


class ReplaceCartLineFormSet(BaseFormSet):
    '''
    Formset for all CartLines in the cart instance.
    '''
    absolute_max = 9999
    can_delete = False
    can_order = False
    extra = 0
    form = ReplaceCartLineForm
    max_num = None

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        kwargs['initial'] = [{'quantity': cart_line.get_quantity()}
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
