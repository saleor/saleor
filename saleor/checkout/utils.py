"""Cart-related utility functions."""
from datetime import date, timedelta
from functools import wraps
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.utils.encoding import smart_text
from django.utils.translation import get_language, pgettext, pgettext_lazy
from prices import TaxedMoneyRange

from . import AddressType, logger
from ..account.forms import get_address_form
from ..account.models import Address
from ..account.utils import store_user_address
from ..core.exceptions import InsufficientStock
from ..core.i18n import ANY_COUNTRY
from ..core.utils import to_local_currency
from ..core.utils.taxes import ZERO_MONEY, get_taxes_for_country
from ..discount import VoucherType
from ..discount.models import NotApplicable, Voucher
from ..discount.utils import (
    get_products_voucher_discount, get_shipping_voucher_discount,
    get_value_voucher_discount, increase_voucher_usage)
from ..order.models import Order
from ..shipping.models import ShippingMethod
from .forms import (
    AddressChoiceForm, AnonymousUserBillingForm, AnonymousUserShippingForm,
    BillingAddressChoiceForm)
from .models import Cart

COOKIE_NAME = 'cart'


def set_cart_cookie(simple_cart, response):
    """Update response with a cart token cookie."""
    # FIXME: document why session is not used
    max_age = int(timedelta(days=30).total_seconds())
    response.set_signed_cookie(COOKIE_NAME, simple_cart.token, max_age=max_age)


def contains_unavailable_variants(cart):
    """Return `True` if cart contains any unfulfillable lines."""
    try:
        for line in cart:
            line.variant.check_quantity(line.quantity)
    except InsufficientStock:
        return True
    return False


def token_is_valid(token):
    """Validate a cart token."""
    if token is None:
        return False
    if isinstance(token, UUID):
        return True
    try:
        UUID(token)
    except ValueError:
        return False
    return True


def remove_unavailable_variants(cart):
    """Remove any unavailable items from cart."""
    for line in cart:
        try:
            add_variant_to_cart(
                cart, line.variant, line.quantity, replace=True)
        except InsufficientStock as e:
            quantity = e.item.quantity_available
            add_variant_to_cart(cart, line.variant, quantity, replace=True)


def get_variant_prices_from_lines(lines):
    """Get's price of each individual item within the lines."""
    return [
        line.variant.get_price()
        for line in lines
        for item in range(line.quantity)]


def get_prices_of_discounted_products(lines, discounted_products):
    """Get prices of variants belonging to the discounted products."""
    # If there's no discounted_products,
    # it means that all products are discounted
    if discounted_products:
        lines = (
            line for line in lines
            if line.variant.product in discounted_products)
    return get_variant_prices_from_lines(lines)


def get_prices_of_products_in_discounted_collections(
        lines, discounted_collections):
    """Get prices of variants belonging to the discounted collections."""
    # If there's no discounted collections,
    # it means that all of them are discounted
    if discounted_collections:
        discounted_collections = set(discounted_collections)
        lines = (
            line for line in lines
            if line.variant and
            set(line.variant.product.collections.all()).intersection(
                discounted_collections))
    return get_variant_prices_from_lines(lines)


def get_prices_of_products_in_discounted_categories(
        lines, discounted_categories):
    """Get prices of variants belonging to the discounted categories.

    Product must be assigned directly to the discounted category, assigning
    product to child category won't work.
    """
    # If there's no discounted collections,
    # it means that all of them are discounted
    if discounted_categories:
        discounted_categories = set(discounted_categories)
        lines = (
            line for line in lines
            if line.variant and
            line.variant.product.category in discounted_categories)
    return get_variant_prices_from_lines(lines)


def check_product_availability_and_warn(request, cart):
    """Warn if cart contains any lines that cannot be fulfilled."""
    if contains_unavailable_variants(cart):
        msg = pgettext_lazy(
            'Cart warning message',
            'Sorry. We don\'t have that many items in stock. '
            'Quantity was set to maximum available for now.')
        messages.warning(request, msg)
        remove_unavailable_variants(cart)


def find_and_assign_anonymous_cart(queryset=Cart.objects.all()):
    """Assign cart from cookie to request user."""
    def get_cart(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            token = request.get_signed_cookie(COOKIE_NAME, default=None)
            if not token_is_valid(token):
                return response
            cart = get_anonymous_cart_from_token(
                token=token, cart_queryset=queryset)
            if cart is None:
                return response
            if request.user.is_authenticated:
                with transaction.atomic():
                    change_cart_user(cart, request.user)
                    carts_to_close = Cart.objects.filter(user=request.user)
                    carts_to_close = carts_to_close.exclude(token=token)
                    carts_to_close.delete()
                response.delete_cookie(COOKIE_NAME)
            return response

        return func
    return get_cart


def get_or_create_anonymous_cart_from_token(
        token, cart_queryset=Cart.objects.all()):
    """Return an open unassigned cart with given token or create a new one."""
    return cart_queryset.filter(token=token, user=None).get_or_create(
        defaults={'user': None})[0]


def get_or_create_user_cart(user, cart_queryset=Cart.objects.all()):
    """Return an open cart for given user or create a new one."""
    defaults = {
        'shipping_address': user.default_shipping_address,
        'billing_address': user.default_billing_address}
    return cart_queryset.get_or_create(user=user, defaults=defaults)[0]


def get_anonymous_cart_from_token(token, cart_queryset=Cart.objects.all()):
    """Return an open unassigned cart with given token if any."""
    return cart_queryset.filter(token=token, user=None).first()


def get_user_cart(user, cart_queryset=Cart.objects.all()):
    """Return an open cart for given user if any."""
    return cart_queryset.filter(user=user).first()


def get_or_create_cart_from_request(request, cart_queryset=Cart.objects.all()):
    """Fetch cart from database or create a new one based on cookie."""
    if request.user.is_authenticated:
        return get_or_create_user_cart(request.user, cart_queryset)
    token = request.get_signed_cookie(COOKIE_NAME, default=None)
    return get_or_create_anonymous_cart_from_token(token, cart_queryset)


def get_cart_from_request(request, cart_queryset=Cart.objects.all()):
    """Fetch cart from database or return a new instance based on cookie."""
    if request.user.is_authenticated:
        cart = get_user_cart(request.user, cart_queryset)
        user = request.user
    else:
        token = request.get_signed_cookie(COOKIE_NAME, default=None)
        cart = get_anonymous_cart_from_token(token, cart_queryset)
        user = None
    if cart is not None:
        return cart
    if user:
        return Cart(user=user)
    return Cart()


def get_or_create_db_cart(cart_queryset=Cart.objects.all()):
    """Decorate view to always receive a saved cart instance.

    Changes the view signature from `func(request, ...)` to
    `func(request, cart, ...)`.

    If no matching cart is found, one will be created and a cookie will be set
    for users who are not logged in.
    """
    # FIXME: behave like middleware and assign cart to request instead
    def get_cart(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            cart = get_or_create_cart_from_request(request, cart_queryset)
            response = view(request, cart, *args, **kwargs)
            if not request.user.is_authenticated:
                set_cart_cookie(cart, response)
            return response
        return func
    return get_cart


def get_or_empty_db_cart(cart_queryset=Cart.objects.all()):
    """Decorate view to receive a cart if one exists.

    Changes the view signature from `func(request, ...)` to
    `func(request, cart, ...)`.

    If no matching cart is found, an unsaved `Cart` instance will be used.
    """
    # FIXME: behave like middleware and assign cart to request instead
    def get_cart(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            cart = get_cart_from_request(request, cart_queryset)
            return view(request, cart, *args, **kwargs)
        return func
    return get_cart


def get_cart_data(cart, shipping_range, currency, discounts, taxes):
    """Return a JSON-serializable representation of the cart."""
    cart_total = None
    local_cart_total = None
    shipping_required = False
    total_with_shipping = None
    local_total_with_shipping = None
    if cart:
        cart_total = cart.get_subtotal(discounts, taxes)
        local_cart_total = to_local_currency(cart_total, currency)
        shipping_required = cart.is_shipping_required()
        total_with_shipping = TaxedMoneyRange(
            start=cart_total, stop=cart_total)
        if shipping_required and shipping_range:
            total_with_shipping = shipping_range + cart_total
        local_total_with_shipping = to_local_currency(
            total_with_shipping, currency)

    return {
        'cart_total': cart_total,
        'local_cart_total': local_cart_total,
        'shipping_required': shipping_required,
        'total_with_shipping': total_with_shipping,
        'local_total_with_shipping': local_total_with_shipping}


def find_open_cart_for_user(user):
    """Find an open cart for the given user."""
    carts = user.carts.all()
    open_cart = carts.first()
    if len(carts) > 1:
        logger.warning('%s has more than one open basket', user)
        carts.exclude(token=open_cart.token).delete()
    return open_cart


def change_cart_user(cart, user):
    """Assign cart to a user.

    If the user already has an open cart assigned, cancel it.
    """
    open_cart = find_open_cart_for_user(user)
    if open_cart is not None:
        open_cart.delete()
    cart.user = user
    cart.shipping_address = user.default_shipping_address
    cart.billing_address = user.default_billing_address
    cart.save(update_fields=['user', 'shipping_address', 'billing_address'])


def update_cart_quantity(cart):
    """Update the total quantity in cart."""
    total_lines = cart.lines.aggregate(
        total_quantity=Sum('quantity'))['total_quantity']
    if not total_lines:
        total_lines = 0
    cart.quantity = total_lines
    cart.save(update_fields=['quantity'])


def add_variant_to_cart(
        cart, variant, quantity=1, replace=False, check_quantity=True):
    """Add a product variant to cart.

    The `data` parameter may be used to differentiate between items with
    different customization options.

    If `replace` is truthy then any previous quantity is discarded instead
    of added to.
    """
    line, _ = cart.lines.get_or_create(
        variant=variant, defaults={'quantity': 0, 'data': {}})
    new_quantity = quantity if replace else (quantity + line.quantity)

    if new_quantity < 0:
        raise ValueError('%r is not a valid quantity (results in %r)' % (
            quantity, new_quantity))

    if new_quantity == 0:
        line.delete()
    else:
        if check_quantity:
            variant.check_quantity(new_quantity)

        line.quantity = new_quantity
        line.save(update_fields=['quantity'])

    update_cart_quantity(cart)


def get_shipping_address_forms(cart, user_addresses, data, country):
    """Forms initialized with data depending on shipping address in cart."""
    shipping_address = (
        cart.shipping_address or cart.user.default_shipping_address)

    if shipping_address and shipping_address in user_addresses:
        address_form, preview = get_address_form(
            data, country_code=country.code,
            initial={'country': country})
        addresses_form = AddressChoiceForm(
            data, addresses=user_addresses,
            initial={'address': shipping_address.id})
    elif shipping_address:
        address_form, preview = get_address_form(
            data, country_code=shipping_address.country.code,
            instance=shipping_address)
        addresses_form = AddressChoiceForm(
            data, addresses=user_addresses)
    else:
        address_form, preview = get_address_form(
            data, country_code=country.code,
            initial={'country': country})
        addresses_form = AddressChoiceForm(
            data, addresses=user_addresses)

    return address_form, addresses_form, preview


def update_shipping_address_in_cart(cart, user_addresses, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, addresses_form, preview = (
        get_shipping_address_forms(cart, user_addresses, data, country))

    updated = False

    if addresses_form.is_valid() and not preview:
        use_existing_address = (
            addresses_form.cleaned_data['address'] !=
            AddressChoiceForm.NEW_ADDRESS)

        if use_existing_address:
            address_id = addresses_form.cleaned_data['address']
            address = Address.objects.get(id=address_id)
            change_shipping_address_in_cart(cart, address)
            updated = True

        elif address_form.is_valid():
            address = address_form.save()
            change_shipping_address_in_cart(cart, address)
            updated = True

    return addresses_form, address_form, updated


def update_shipping_address_in_anonymous_cart(cart, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, preview = get_address_form(
        data, country_code=country.code,
        autocomplete_type='shipping',
        instance=cart.shipping_address,
        initial={'country': country})
    user_form = AnonymousUserShippingForm(
        data if not preview else None, instance=cart)

    updated = False

    if user_form.is_valid() and address_form.is_valid():
        user_form.save()
        address = address_form.save()
        change_shipping_address_in_cart(cart, address)
        updated = True

    return user_form, address_form, updated


def get_billing_forms_with_shipping(cart, data, user_addresses, country):
    """Get billing form based on a the current billing and shipping data."""
    shipping_address = cart.shipping_address
    billing_address = cart.billing_address or Address(country=country)

    if not billing_address.id or billing_address == shipping_address:
        address_form, preview = get_address_form(
            data, country_code=shipping_address.country.code,
            autocomplete_type='billing',
            initial={'country': shipping_address.country})
        addresses_form = BillingAddressChoiceForm(
            data, addresses=user_addresses, initial={
                'address': BillingAddressChoiceForm.SHIPPING_ADDRESS})
    elif billing_address in user_addresses:
        address_form, preview = get_address_form(
            data, country_code=billing_address.country.code,
            autocomplete_type='billing',
            initial={'country': billing_address.country})
        addresses_form = BillingAddressChoiceForm(
            data, addresses=user_addresses, initial={
                'address': billing_address.id})
    else:
        address_form, preview = get_address_form(
            data, country_code=billing_address.country.code,
            autocomplete_type='billing',
            initial={'country': billing_address.country},
            instance=billing_address)
        addresses_form = BillingAddressChoiceForm(
            data, addresses=user_addresses, initial={
                'address': BillingAddressChoiceForm.NEW_ADDRESS})

    return address_form, addresses_form, preview


def update_billing_address_in_cart_with_shipping(
        cart, user_addresses, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, addresses_form, preview = get_billing_forms_with_shipping(
        cart, data, user_addresses, country)

    updated = False

    if addresses_form.is_valid() and not preview:
        address = None
        address_id = addresses_form.cleaned_data['address']

        if address_id == BillingAddressChoiceForm.SHIPPING_ADDRESS:
            if cart.user and cart.shipping_address in user_addresses:
                address = cart.shipping_address
            else:
                address = cart.shipping_address.get_copy()
        elif address_id != BillingAddressChoiceForm.NEW_ADDRESS:
            address = user_addresses.get(id=address_id)
        elif address_form.is_valid():
            address = address_form.save()

        if address:
            change_billing_address_in_cart(cart, address)
            updated = True

    return addresses_form, address_form, updated


def get_anonymous_summary_without_shipping_forms(cart, data, country):
    """Forms initialized with data depending on addresses in cart."""
    billing_address = cart.billing_address

    if billing_address:
        address_form, preview = get_address_form(
            data, country_code=billing_address.country.code,
            autocomplete_type='billing', instance=billing_address)
    else:
        address_form, preview = get_address_form(
            data, country_code=country.code,
            autocomplete_type='billing', initial={'country': country})

    return address_form, preview


def update_billing_address_in_anonymous_cart(cart, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, preview = get_anonymous_summary_without_shipping_forms(
        cart, data, country)
    user_form = AnonymousUserBillingForm(data, instance=cart)

    updated = False

    if user_form.is_valid() and address_form.is_valid() and not preview:
        user_form.save()
        address = address_form.save()
        change_billing_address_in_cart(cart, address)
        updated = True

    return user_form, address_form, updated


def get_summary_without_shipping_forms(cart, user_addresses, data, country):
    """Forms initialized with data depending on addresses in cart."""
    billing_address = cart.billing_address

    if billing_address and billing_address in user_addresses:
        address_form, preview = get_address_form(
            data,
            autocomplete_type='billing',
            country_code=billing_address.country.code,
            initial={'country': billing_address.country})
        initial_address = billing_address.id
    elif billing_address:
        address_form, preview = get_address_form(
            data,
            autocomplete_type='billing',
            country_code=billing_address.country.code,
            initial={'country': billing_address.country},
            instance=billing_address)
        initial_address = AddressChoiceForm.NEW_ADDRESS
    else:
        address_form, preview = get_address_form(
            data,
            autocomplete_type='billing',
            country_code=country.code,
            initial={'country': country})
        if cart.user and cart.user.default_billing_address:
            initial_address = cart.user.default_billing_address.id
        else:
            initial_address = AddressChoiceForm.NEW_ADDRESS

    addresses_form = AddressChoiceForm(
        data, addresses=user_addresses, initial={'address': initial_address})
    return address_form, addresses_form, preview


def update_billing_address_in_cart(cart, user_addresses, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, addresses_form, preview = (
        get_summary_without_shipping_forms(
            cart, user_addresses, data, country))

    updated = False

    if addresses_form.is_valid():
        use_existing_address = (
            addresses_form.cleaned_data['address'] !=
            AddressChoiceForm.NEW_ADDRESS)

        if use_existing_address:
            address_id = addresses_form.cleaned_data['address']
            address = Address.objects.get(id=address_id)
            change_billing_address_in_cart(cart, address)
            updated = True

        elif address_form.is_valid():
            address = address_form.save()
            change_billing_address_in_cart(cart, address)
            updated = True

    return addresses_form, address_form, updated


def _check_new_cart_address(cart, address, address_type):
    """Check if and address in cart has changed and if to remove old one."""
    if address_type == AddressType.BILLING:
        old_address = cart.billing_address
    else:
        old_address = cart.shipping_address

    has_address_changed = any([
        not address and old_address,
        address and not old_address,
        address and old_address and address != old_address])

    remove_old_address = (
        has_address_changed and
        old_address is not None and
        (not cart.user or old_address not in cart.user.addresses.all()))

    return has_address_changed, remove_old_address


def change_billing_address_in_cart(cart, address):
    """Save billing address in cart if changed.

    Remove previously saved address if not connected to any user.
    """
    changed, remove = _check_new_cart_address(
        cart, address, AddressType.BILLING)
    if changed:
        if remove:
            cart.billing_address.delete()
        cart.billing_address = address
        cart.save(update_fields=['billing_address'])


def change_shipping_address_in_cart(cart, address):
    """Save shipping address in cart if changed.

    Remove previously saved address if not connected to any user.
    """
    changed, remove = _check_new_cart_address(
        cart, address, AddressType.SHIPPING)
    if changed:
        if remove:
            cart.shipping_address.delete()
        cart.shipping_address = address
        cart.save(update_fields=['shipping_address'])


def get_cart_data_for_checkout(cart, discounts, taxes):
    """Data shared between views in checkout process."""
    lines = [(line, line.get_total(discounts, taxes)) for line in cart]
    subtotal = cart.get_subtotal(discounts, taxes)
    total = cart.get_total(discounts, taxes)
    shipping_price = cart.get_shipping_price(taxes)
    return {
        'cart': cart,
        'cart_are_taxes_handled': bool(taxes),
        'cart_lines': lines,
        'cart_shipping_price': shipping_price,
        'cart_subtotal': subtotal,
        'cart_total': total}


def _get_shipping_voucher_discount_for_cart(voucher, cart):
    """Calculate discount value for a voucher of shipping type."""
    if not cart.is_shipping_required():
        msg = pgettext(
            'Voucher not applicable',
            'Your order does not require shipping.')
        raise NotApplicable(msg)
    shipping_method = cart.shipping_method
    if not shipping_method:
        msg = pgettext(
            'Voucher not applicable',
            'Please select a shipping method first.')
        raise NotApplicable(msg)
    not_valid_for_country = all([
        voucher.countries, ANY_COUNTRY not in voucher.countries,
        cart.shipping_address.country.code not in voucher.countries])
    if not_valid_for_country:
        msg = pgettext(
            'Voucher not applicable',
            'This offer is not valid in your country.')
        raise NotApplicable(msg)
    return get_shipping_voucher_discount(
        voucher, cart.get_subtotal(), shipping_method.get_total())


def _get_products_voucher_discount(order_or_cart, voucher):
    """Calculate products discount value for a voucher, depending on its type.
    """
    if voucher.type == VoucherType.PRODUCT:
        prices = get_prices_of_discounted_products(
            order_or_cart.lines.all(), voucher.products.all())
    elif voucher.type == VoucherType.COLLECTION:
        prices = get_prices_of_products_in_discounted_collections(
            order_or_cart.lines.all(), voucher.collections.all())
    elif voucher.type == VoucherType.CATEGORY:
        prices = get_prices_of_products_in_discounted_categories(
            order_or_cart.lines.all(), voucher.categories.all())
    if not prices:
        msg = pgettext(
            'Voucher not applicable',
            'This offer is only valid for selected items.')
        raise NotApplicable(msg)
    return get_products_voucher_discount(voucher, prices)


def get_voucher_discount_for_cart(voucher, cart):
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    if voucher.type == VoucherType.VALUE:
        return get_value_voucher_discount(voucher, cart.get_subtotal())
    if voucher.type == VoucherType.SHIPPING:
        return _get_shipping_voucher_discount_for_cart(voucher, cart)
    if voucher.type in (
            VoucherType.PRODUCT, VoucherType.COLLECTION, VoucherType.CATEGORY):
        return _get_products_voucher_discount(cart, voucher)
    raise NotImplementedError('Unknown discount type')


def get_voucher_for_cart(cart, vouchers=None):
    """Return voucher with voucher code saved in cart if active or None."""
    if cart.voucher_code is not None:
        if vouchers is None:
            vouchers = Voucher.objects.active(date=date.today())
        try:
            return vouchers.get(code=cart.voucher_code)
        except Voucher.DoesNotExist:
            return None
    return None


def recalculate_cart_discount(cart, discounts, taxes):
    """Recalculate `cart.discount` based on the voucher.

    Will clear both voucher and discount if the discount is no longer
    applicable.
    """
    voucher = get_voucher_for_cart(cart)
    if voucher is not None:
        try:
            discount = get_voucher_discount_for_cart(voucher, cart)
        except NotApplicable:
            remove_voucher_from_cart(cart)
        else:
            subtotal = cart.get_subtotal(discounts, taxes).gross
            cart.discount_amount = min(discount, subtotal)
            cart.discount_name = str(voucher)
            cart.translated_discount_name = (
                voucher.translated.name
                if voucher.translated.name != voucher.name else '')
            cart.save(
                update_fields=[
                    'translated_discount_name',
                    'discount_amount', 'discount_name'])
    else:
        remove_voucher_from_cart(cart)


def remove_voucher_from_cart(cart):
    """Remove voucher data from cart."""
    cart.voucher_code = None
    cart.discount_name = None
    cart.translated_discount_name = None
    cart.discount_amount = ZERO_MONEY
    cart.save(
        update_fields=[
            'voucher_code', 'discount_name', 'translated_discount_name',
            'discount_amount'])


def get_taxes_for_cart(cart, default_taxes):
    """Return taxes (if handled) due to shipping address or default one."""
    if not settings.VATLAYER_ACCESS_KEY:
        return None

    if cart.shipping_address:
        return get_taxes_for_country(cart.shipping_address.country)

    return default_taxes


def is_valid_shipping_method(cart, taxes, discounts):
    """Check if shipping method is valid and remove (if not)."""
    if not cart.shipping_method:
        return False

    valid_methods = ShippingMethod.objects.applicable_shipping_methods(
        price=cart.get_subtotal(discounts, taxes).gross,
        weight=cart.get_total_weight(),
        country_code=cart.shipping_address.country.code)
    if cart.shipping_method not in valid_methods:
        clear_shipping_method(cart)
        return False
    return True


def clear_shipping_method(cart):
    cart.shipping_method = None
    cart.save(update_fields=['shipping_method'])


def _process_voucher_data_for_order(cart):
    """Fetch, process and return voucher/discount data from cart."""
    vouchers = Voucher.objects.active(date=date.today()).select_for_update()
    voucher = get_voucher_for_cart(cart, vouchers)

    if cart.voucher_code and not voucher:
        msg = pgettext(
            'Voucher not applicable',
            'Voucher expired in meantime. Order placement aborted.')
        raise NotApplicable(msg)

    if not voucher:
        return {}

    increase_voucher_usage(voucher)
    return {
        'voucher': voucher,
        'discount_amount': cart.discount_amount,
        'discount_name': cart.discount_name,
        'translated_discount_name': cart.translated_discount_name}


def _process_shipping_data_for_order(cart, taxes):
    """Fetch, process and return shipping data from cart."""
    if not cart.is_shipping_required():
        return {}

    shipping_address = cart.shipping_address

    if cart.user:
        store_user_address(cart.user, shipping_address, AddressType.SHIPPING)
        if cart.user.addresses.filter(pk=shipping_address.pk).exists():
            shipping_address = shipping_address.get_copy()

    return {
        'shipping_address': shipping_address,
        'shipping_method': cart.shipping_method,
        'shipping_method_name': smart_text(cart.shipping_method),
        'shipping_price': cart.get_shipping_price(taxes),
        'weight': cart.get_total_weight()}


def _process_user_data_for_order(cart):
    """Fetch, process and return shipping data from cart."""
    billing_address = cart.billing_address

    if cart.user:
        store_user_address(cart.user, billing_address, AddressType.BILLING)
        if cart.user.addresses.filter(pk=billing_address.pk).exists():
            billing_address = billing_address.get_copy()

    return {
        'user': cart.user,
        'user_email': cart.user.email if cart.user else cart.email,
        'billing_address': billing_address}


def _fill_order_with_cart_data(order, cart, discounts, taxes):
    """Fill an order with data (variants, note) from cart."""
    from ..order.utils import add_variant_to_order

    for line in cart:
        add_variant_to_order(
            order, line.variant, line.quantity, discounts, taxes)

    cart.payment_methods.update(order=order)

    if cart.note:
        order.customer_note = cart.note
        order.save(update_fields=['customer_note'])


@transaction.atomic
def create_order(cart, tracking_code, discounts, taxes):
    """Create an order from the cart.

    Each order will get a private copy of both the billing and the shipping
    address (if shipping).

    If any of the addresses is new and the user is logged in the address
    will also get saved to that user's address book.

    Current user's language is saved in the order so we can later determine
    which language to use when sending email.
    """
    # FIXME: save locale along with the language
    try:
        order_data = _process_voucher_data_for_order(cart)
    except NotApplicable:
        return None

    order_data.update(_process_shipping_data_for_order(cart, taxes))
    order_data.update(_process_user_data_for_order(cart))
    order_data.update({
        'language_code': get_language(),
        'tracking_client_id': tracking_code,
        'total': cart.get_total(discounts, taxes)})

    order = Order.objects.create(**order_data)

    _fill_order_with_cart_data(order, cart, discounts, taxes)
    return order


def is_fully_paid(cart: Cart):
    payment_methods = cart.payment_methods.filter(is_active=True)
    total_paid = sum(
        [p.captured_amount.amount for p in payment_methods])
    return total_paid >= cart.get_total().gross.amount


def ready_to_place_order(cart: Cart):
    if cart.is_shipping_required():
        if not cart.shipping_method:
            return False, pgettext_lazy(
                'order placement_error', 'Shipping method is not set')
        if not cart.shipping_address:
            return False, pgettext_lazy(
                'order placement error', 'Shipping address is not set')
        # FIXME Check if shipping method is valid for the shipping address
    if not is_fully_paid(cart):
        return False, pgettext_lazy(
            'order placement error', 'Checkout is not fully paid')
    return True, None
