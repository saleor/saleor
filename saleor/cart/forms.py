from __future__ import unicode_literals
import json

from django import forms
from django.core.exceptions import ObjectDoesNotExist, NON_FIELD_ERRORS
from django.forms import inlineformset_factory
from django.utils.translation import pgettext_lazy, ugettext_lazy
from satchless.item import InsufficientStock

from .models import Cart, CartLine


class QuantityField(forms.IntegerField):

    def __init__(self, **kwargs):
        super(QuantityField, self).__init__(min_value=0, max_value=999,
                                            initial=1, **kwargs)


class AddToCartForm(forms.Form):
    """Add-to-cart form

    Allows selection of a product variant and quantity.
    The save method adds it to the cart.
    """
    quantity = QuantityField(label=pgettext_lazy('Form field', 'Quantity'))
    error_messages = {
        'not-available': ugettext_lazy(
            'Sorry. This product is currently not available.'
        ),
        'empty-stock': ugettext_lazy(
            'Sorry. This product is currently out of stock.'
        ),
        'variant-does-not-exists': ugettext_lazy(
            'Oops. We could not find that product.'
        ),
        'insufficient-stock': ugettext_lazy(
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
                product_variant.check_quantity(new_quantity)
            except InsufficientStock as e:
                remaining = e.item.get_stock_quantity() - used_quantity
                if remaining:
                    msg = self.error_messages['insufficient-stock']
                else:
                    msg = self.error_messages['empty-stock']
                self.add_error('quantity', msg % {'remaining': remaining})
        return cleaned_data

    def save(self):
        """Adds the selected product variant and quantity to the cart"""
        product_variant = self.get_variant(self.cleaned_data)
        real_cart = Cart.objects.get_or_create(token=self.cart.token)[0]
        return real_cart.add(product=product_variant,
                             quantity=self.cleaned_data['quantity'])

    def get_variant(self, cleaned_data):
        raise NotImplementedError()


class ReplaceCartLineForm(AddToCartForm):
    """Replace quantity form

    Similar to AddToCartForm but its save method replaces the quantity.
    """
    def __init__(self, *args, **kwargs):
        super(ReplaceCartLineForm, self).__init__(*args, **kwargs)
        self.cart_line = self.cart.get_line(self.product)
        self.fields['quantity'].widget.attrs = {
            'min': 1, 'max': self.product.get_stock_quantity()}

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        try:
            self.cart.check_quantity(self.product, quantity, None)
        except InsufficientStock as e:
            msg = self.error_messages['insufficient-stock']
            raise forms.ValidationError(msg % {
                'remaining': e.item.get_stock_quantity()})
        return quantity

    def clean(self):
        # explicitly skip parent's implementation
        # pylint: disable=E1003
        return super(AddToCartForm, self).clean()

    def get_variant(self, cleaned_data):
        """In cart formsets product is already the variant we want"""
        return self.product

    def save(self):
        """Replaces the selected product's quantity in cart"""
        product_variant = self.get_variant(self.cleaned_data)
        return self.cart.add(product_variant, self.cleaned_data['quantity'],
                             replace=True)


class CartLineForm(forms.ModelForm):
    quantity = QuantityField()

    class Meta:
        fields = []
        model = CartLine

    def clean(self):
        data = super(CartLineForm, self).clean()
        quantity = data.get('quantity')
        if quantity == 0:
            data['DELETE'] = True
        return data


class CartBaseFormSet(forms.BaseInlineFormSet):
    def save(self, commit=True):
        super(CartBaseFormSet, self).save(commit)
        self.instance.update_quantity()

CartFormset = inlineformset_factory(
    Cart, CartLine, form=CartLineForm, formset=CartBaseFormSet,
    fields=('quantity',), extra=0)
