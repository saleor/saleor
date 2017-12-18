"""Cart-related forms and fields."""
from django import forms
from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ObjectDoesNotExist
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_countries.fields import LazyTypedChoiceField, countries
from satchless.item import InsufficientStock

from ..shipping.utils import get_shipment_options


class QuantityField(forms.IntegerField):
    """A specialized integer field with initial quantity and min/max values."""

    def __init__(self, **kwargs):
        super().__init__(
            min_value=0, max_value=settings.MAX_CART_LINE_QUANTITY,
            initial=1, **kwargs)


class AddToCartForm(forms.Form):
    """Add-to-cart form.

    Allows selection of a product variant and quantity.

    The save method adds it to the cart.
    """

    quantity = QuantityField(
        label=pgettext_lazy('Add to cart form field label', 'Quantity'))
    error_messages = {
        'not-available': pgettext_lazy(
            'Add to cart form error',
            'Sorry. This product is currently not available.'),
        'empty-stock': pgettext_lazy(
            'Add to cart form error',
            'Sorry. This product is currently out of stock.'),
        'variant-does-not-exists': pgettext_lazy(
            'Add to cart form error',
            'Oops. We could not find that product.'),
        'insufficient-stock': npgettext_lazy(
            'Add to cart form error',
            'Only %d remaining in stock.',
            'Only %d remaining in stock.')}

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        self.product = kwargs.pop('product')
        self.discounts = kwargs.pop('discounts', ())
        super().__init__(*args, **kwargs)

    def clean(self):
        """Clean the form.

        Makes sure the total quantity in cart (taking into account what was
        already there) does not exceed available quantity.
        """
        cleaned_data = super().clean()
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
                    self.add_error('quantity', msg % remaining)
                else:
                    msg = self.error_messages['empty-stock']
                    self.add_error('quantity', msg)
        return cleaned_data

    def save(self):
        """Add the selected product variant and quantity to the cart."""
        product_variant = self.get_variant(self.cleaned_data)
        return self.cart.add(variant=product_variant,
                             quantity=self.cleaned_data['quantity'])

    def get_variant(self, cleaned_data):
        """Return a product variant that matches submitted values.

        This allows specialized implementations to select the variant based on
        multiple fields (like size and color) instead of having a single
        variant selection widget.
        """
        raise NotImplementedError()


class ReplaceCartLineForm(AddToCartForm):
    """Replace quantity in cart form.

    Similar to AddToCartForm but its save method replaces the quantity.
    """

    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant')
        kwargs['product'] = self.variant.product
        super().__init__(*args, **kwargs)
        self.cart_line = self.cart.get_line(self.variant)
        self.fields['quantity'].widget.attrs = {
            'min': 1, 'max': settings.MAX_CART_LINE_QUANTITY}

    def clean_quantity(self):
        """Clean the quantity field.

        Checks if target quantity does not exceed the currently available
        quantity.
        """
        quantity = self.cleaned_data['quantity']
        try:
            self.variant.check_quantity(quantity)
        except InsufficientStock as e:
            msg = self.error_messages['insufficient-stock']
            raise forms.ValidationError(
                msg % e.item.get_stock_quantity())
        return quantity

    def clean(self):
        """Clean the form skipping the add-to-form checks."""
        # explicitly skip parent's implementation
        # pylint: disable=E1003
        return super(AddToCartForm, self).clean()

    def get_variant(self, cleaned_data):
        """Return the matching variant.

        In this case we explicitly know the variant as we're modifying an
        existing line in cart.
        """
        return self.variant

    def save(self):
        """Replace the selected product's quantity in cart."""
        product_variant = self.get_variant(self.cleaned_data)
        return self.cart.add(product_variant, self.cleaned_data['quantity'],
                             replace=True)


class CountryForm(forms.Form):
    """Country selection form."""

    country = LazyTypedChoiceField(
        label=pgettext_lazy('Country form field label', 'Country'),
        choices=countries)

    def get_shipment_options(self):
        """Return a list of shipping methods for the selected country."""
        code = self.cleaned_data['country']
        return get_shipment_options(code)
