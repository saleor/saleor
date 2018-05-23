"""Cart-related ORM models."""
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.encoding import smart_str
from django.utils.timezone import now
from django_prices.models import MoneyField
from jsonfield import JSONField

from . import CartStatus, logger
from ..account.models import Address
from ..core.utils.taxes import ZERO_TAXED_MONEY
from ..shipping.models import ShippingMethodCountry

CENTS = Decimal('0.01')


def find_open_cart_for_user(user):
    """Find an open cart for the given user."""
    carts = user.carts.open()
    if len(carts) > 1:
        logger.warning('%s has more than one open basket', user)
        for cart in carts[1:]:
            cart.change_status(CartStatus.CANCELED)
    return carts.first()


class CartQueryset(models.QuerySet):
    """A specialized queryset for dealing with carts."""

    def anonymous(self):
        """Return unassigned carts."""
        return self.filter(user=None)

    def open(self):
        """Return `OPEN` carts."""
        return self.filter(status=CartStatus.OPEN)

    def canceled(self):
        """Return `CANCELED` carts."""
        return self.filter(status=CartStatus.CANCELED)

    def for_display(self):
        """Annotate the queryset for display purposes.

        Prefetches additional data from the database to avoid the n+1 queries
        problem.
        """
        return self.prefetch_related(
            'lines__variant__product__category',
            'lines__variant__product__images',
            'lines__variant__product__product_type__product_attributes__values')  # noqa


class Cart(models.Model):
    """A shopping cart."""

    status = models.CharField(
        max_length=32, choices=CartStatus.CHOICES, default=CartStatus.OPEN)
    created = models.DateTimeField(auto_now_add=True)
    last_status_change = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='carts',
        on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    token = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    total = MoneyField(
        currency=settings.DEFAULT_CURRENCY, max_digits=12,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES, default=0)
    quantity = models.PositiveIntegerField(default=0)

    # data used for handling checkout process
    user_email = models.EmailField(blank=True, default='')
    billing_address = models.ForeignKey(
        Address, related_name='+', editable=False, null=True,
        on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(
        Address, related_name='+', editable=False, null=True,
        on_delete=models.SET_NULL)
    shipping_method = models.ForeignKey(
        ShippingMethodCountry, blank=True, null=True, related_name='carts',
        on_delete=models.SET_NULL)
    note = models.TextField(blank=True, default='')
    discount_amount = MoneyField(
        currency=settings.DEFAULT_CURRENCY, max_digits=12,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES, default=0)
    discount_name = models.CharField(max_length=255, blank=True, null=True)
    voucher_code = models.CharField(max_length=12, blank=True, null=True)

    objects = CartQueryset.as_manager()

    class Meta:
        ordering = ('-last_status_change',)

    def __repr__(self):
        return 'Cart(quantity=%s)' % (self.quantity,)

    def __len__(self):
        return self.lines.count()

    def update_quantity(self):
        """Recalculate cart quantity based on lines."""
        total_lines = self.count()['total_quantity']
        if not total_lines:
            total_lines = 0
        self.quantity = total_lines
        self.save(update_fields=['quantity'])

    def change_status(self, status):
        """Change cart status."""
        # FIXME: investigate replacing with django-fsm transitions
        if status not in dict(CartStatus.CHOICES):
            raise ValueError('Not expected status')
        if status != self.status:
            self.status = status
            self.last_status_change = now()
            self.save()

    def change_user(self, user):
        """Assign cart to a user.

        If the user already has an open cart assigned, cancel it.
        """
        open_cart = find_open_cart_for_user(user)
        if open_cart is not None:
            open_cart.change_status(status=CartStatus.CANCELED)
        self.user = user
        self.shipping_address = user.default_shipping_address
        self.save(update_fields=['user', 'shipping_address'])

    def is_shipping_required(self):
        """Return `True` if any of the lines requires shipping."""
        return any(line.is_shipping_required() for line in self.lines.all())

    def get_shipping_price(self, taxes):
        return (
            self.shipping_method.get_total_price(taxes)
            if self.shipping_method and self.is_shipping_required()
            else ZERO_TAXED_MONEY)

    def get_subtotal(self, discounts=None, taxes=None):
        """Return the total cost of the cart prior to shipping."""
        subtotals = (
            line.get_total(discounts, taxes) for line in self.lines.all())
        return sum(subtotals, ZERO_TAXED_MONEY)

    def get_total(self, discounts=None, taxes=None):
        """Return the total cost of the cart."""
        total = self.get_subtotal(discounts, taxes)
        total += self.get_shipping_price(taxes)
        total -= self.discount_amount
        return total

    def count(self):
        """Return the total quantity in cart."""
        lines = self.lines.all()
        return lines.aggregate(total_quantity=models.Sum('quantity'))

    def create_line(self, variant, quantity, data):
        """Create a cart line for given variant, quantity and optional data.

        The `data` parameter may be used to differentiate between items with
        different customization options.
        """
        return self.lines.create(
            variant=variant, quantity=quantity, data=data or {})

    def get_line(self, variant, data=None):
        """Return a line matching the given variant and data if any."""
        all_lines = self.lines.all()
        if data is None:
            data = {}
        line = [
            line for line in all_lines
            if line.variant_id == variant.id and line.data == data]
        if line:
            return line[0]
        return None

    def add(self, variant, quantity=1, data=None, replace=False,
            check_quantity=True):
        """Add a product vartiant to cart.

        The `data` parameter may be used to differentiate between items with
        different customization options.

        If `replace` is truthy then any previous quantity is discarded instead
        of added to.
        """
        cart_line, dummy_created = self.lines.get_or_create(
            variant=variant, defaults={'quantity': 0, 'data': data or {}})
        if replace:
            new_quantity = quantity
        else:
            new_quantity = cart_line.quantity + quantity

        if new_quantity < 0:
            raise ValueError('%r is not a valid quantity (results in %r)' % (
                quantity, new_quantity))

        if check_quantity:
            variant.check_quantity(new_quantity)

        cart_line.quantity = new_quantity

        if not cart_line.quantity:
            cart_line.delete()
        else:
            cart_line.save(update_fields=['quantity'])
        self.update_quantity()


class CartLine(models.Model):
    """A single cart line.

    Multiple lines in the same cart can refer to the same product variant if
    their `data` field is different.
    """

    cart = models.ForeignKey(
        Cart, related_name='lines', on_delete=models.CASCADE)
    variant = models.ForeignKey(
        'product.ProductVariant', related_name='+', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(999)])
    data = JSONField(blank=True, default={})

    class Meta:
        unique_together = ('cart', 'variant', 'data')

    def __str__(self):
        return smart_str(self.variant)

    def __eq__(self, other):
        if not isinstance(other, CartLine):
            return NotImplemented

        return (
            self.variant == other.variant and
            self.quantity == other.quantity and
            self.data == other.data)

    def __ne__(self, other):
        return not self == other  # pragma: no cover

    def __repr__(self):
        return 'CartLine(variant=%r, quantity=%r, data=%r)' % (
            self.variant, self.quantity, self.data)

    def __getstate__(self):
        return self.variant, self.quantity, self.data

    def __setstate__(self, data):
        self.variant, self.quantity, self.data = data

    def get_total(self, discounts=None, taxes=None):
        """Return the total price of this line."""
        amount = self.quantity * self.variant.get_price(discounts, taxes)
        return amount.quantize(CENTS)

    def is_shipping_required(self):
        """Return `True` if the related product variant requires shipping."""
        return self.variant.is_shipping_required()
