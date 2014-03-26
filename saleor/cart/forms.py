from __future__ import unicode_literals
from decimal import Decimal

from django import forms
from django.core.exceptions import ObjectDoesNotExist, NON_FIELD_ERRORS
from django.forms.formsets import BaseFormSet, DEFAULT_MAX_NUM
from django.utils.translation import pgettext, ugettext
from satchless.item import InsufficientStock


class QuantityField(forms.IntegerField):

    def __init__(self, *args, **kwargs):
        super(QuantityField, self).__init__(min_value=0, max_value=999,
                                            initial=1)


class AddToCartForm(forms.Form):
    """
    Class use product and cart instance.
    """
    quantity = QuantityField(label=pgettext('Form field', 'Quantity'))
    error_messages = {
        'empty-stock': ugettext(
            'Sorry. This product is currently out of stock.'
        ),
        'variant-does-not-exists': ugettext(
            'Oops. We could not find that product.'
        ),
        'insufficient-stock': ugettext(
            'Only %(remaining)d remaining in stock.'
        )
    }

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        self.product = kwargs.pop('product')
        super(AddToCartForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddToCartForm, self).clean()
        quantity = cleaned_data.get('quantity')
        if quantity is None:
            return cleaned_data
        try:
            product_variant = self.get_variant(cleaned_data)
        except ObjectDoesNotExist:
            msg = self.error_messages['variant-does-not-exists']
            self.add_error(NON_FIELD_ERRORS, msg)
        else:
            cart_line = self.cart.get_line(product_variant)
            used_quantity = cart_line.quantity if cart_line else 0
            new_quantity = quantity + used_quantity
            try:
                self.cart.check_quantity(
                    product_variant, new_quantity, None)
            except InsufficientStock as e:
                remaining = e.item.stock - used_quantity
                if remaining:
                    msg = self.error_messages['insufficient-stock']
                else:
                    msg = self.error_messages['empty-stock']
                self.add_error('quantity', msg % {'remaining': remaining})
        return cleaned_data

    def save(self):
        """
        Adds CartLine into the Cart instance.
        """
        product_variant = self.get_variant(self.cleaned_data)
        return self.cart.add(product_variant, self.cleaned_data['quantity'])

    def get_variant(self, cleaned_data):
        raise NotImplementedError()

    def add_error(self, name, value):
        errors = self.errors.setdefault(name, self.error_class())
        errors.append(value)


class ReplaceCartLineForm(AddToCartForm):
    """
    Replaces quantity in CartLine.
    """
    def __init__(self, *args, **kwargs):
        super(ReplaceCartLineForm, self).__init__(*args, **kwargs)
        self.cart_line = self.cart.get_line(self.product)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        try:
            self.cart.check_quantity(self.product, quantity, None)
        except InsufficientStock as e:
            msg = self.error_messages['insufficient-stock']
            raise forms.ValidationError(msg % {'remaining': e.item.stock})
        return quantity

    def clean(self):
        return super(AddToCartForm, self).clean()

    def get_variant(self, cleaned_data):
        """In cart formset product is already variant"""
        return self.product

    def save(self):
        """
        Replace quantity.
        """
        return self.cart.add(self.product, self.cleaned_data['quantity'],
                             replace=True)


class ReplaceCartLineFormSet(BaseFormSet):
    """
    Formset for all CartLines in the cart instance.
    """
    absolute_max = 9999
    can_delete = False
    can_order = False
    extra = 0
    form = ReplaceCartLineForm
    max_num = DEFAULT_MAX_NUM
    validate_max = False

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
