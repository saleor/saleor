"""Checkout-related utility functions."""
from datetime import date, timedelta
from functools import wraps
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils.encoding import smart_text
from django.utils.translation import get_language, pgettext, pgettext_lazy
from prices import TaxedMoneyRange

from ..account.forms import get_address_form
from ..account.models import Address, User
from ..account.utils import store_user_address
from ..core.exceptions import InsufficientStock
from ..core.utils import to_local_currency
from ..core.utils.taxes import ZERO_MONEY, get_taxes_for_country
from ..discount import VoucherType
from ..discount.models import NotApplicable, Voucher
from ..discount.utils import (
    get_products_voucher_discount, get_shipping_voucher_discount,
    get_value_voucher_discount, increase_voucher_usage)
from ..order.models import Order
from ..shipping.models import ShippingMethod
from . import AddressType, logger
from .forms import (
    AddressChoiceForm, AnonymousUserBillingForm, AnonymousUserShippingForm,
    BillingAddressChoiceForm)
from .models import Checkout

COOKIE_NAME = 'checkout'


def set_checkout_cookie(simple_checkout, response):
    """Update response with a checkout token cookie."""
    # FIXME: document why session is not used
    max_age = int(timedelta(days=30).total_seconds())
    response.set_signed_cookie(COOKIE_NAME, simple_checkout.token, max_age=max_age)


def contains_unavailable_variants(checkout):
    """Return `True` if checkout contains any unfulfillable lines."""
    try:
        for line in checkout:
            line.variant.check_quantity(line.quantity)
    except InsufficientStock:
        return True
    return False


def token_is_valid(token):
    """Validate a checkout token."""
    if token is None:
        return False
    if isinstance(token, UUID):
        return True
    try:
        UUID(token)
    except ValueError:
        return False
    return True


def remove_unavailable_variants(checkout):
    """Remove any unavailable items from checkout."""
    for line in checkout:
        try:
            add_variant_to_checkout(
                checkout, line.variant, line.quantity, replace=True)
        except InsufficientStock as e:
            quantity = e.item.quantity_available
            add_variant_to_checkout(checkout, line.variant, quantity, replace=True)


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


def check_product_availability_and_warn(request, checkout):
    """Warn if checkout contains any lines that cannot be fulfilled."""
    if contains_unavailable_variants(checkout):
        msg = pgettext_lazy(
            'Checkout warning message',
            'Sorry. We don\'t have that many items in stock. '
            'Quantity was set to maximum available for now.')
        messages.warning(request, msg)
        remove_unavailable_variants(checkout)


def find_and_assign_anonymous_checkout(queryset=Checkout.objects.all()):
    """Assign checkout from cookie to request user."""
    def get_checkout(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            token = request.get_signed_cookie(COOKIE_NAME, default=None)
            if not token_is_valid(token):
                return response
            checkout = get_anonymous_checkout_from_token(
                token=token, checkout_queryset=queryset)
            if checkout is None:
                return response
            if request.user.is_authenticated:
                with transaction.atomic():
                    change_checkout_user(checkout, request.user)
                    checkouts_to_close = Checkout.objects.filter(user=request.user)
                    checkouts_to_close = checkouts_to_close.exclude(token=token)
                    checkouts_to_close.delete()
                response.delete_cookie(COOKIE_NAME)
            return response

        return func
    return get_checkout


def get_or_create_anonymous_checkout_from_token(
        token, checkout_queryset=Checkout.objects.all()):
    """Return an open unassigned checkout with given token or create a new one."""
    return checkout_queryset.filter(token=token, user=None).get_or_create(
        defaults={'user': None})[0]


def get_or_create_user_checkout(user: User, checkout_queryset=Checkout.objects.all()):
    """Return an open checkout for given user or create a new one."""
    defaults = {
        'shipping_address': user.default_shipping_address,
        'billing_address': user.default_billing_address}

    created = False
    checkout = checkout_queryset.filter(user=user).first()
    if checkout is None:
        checkout = Checkout.objects.create(user=user, **defaults)
        created = True
    return checkout, created


def get_anonymous_checkout_from_token(token, checkout_queryset=Checkout.objects.all()):
    """Return an open unassigned checkout with given token if any."""
    return checkout_queryset.filter(token=token, user=None).first()


def get_user_checkout(user, checkout_queryset=Checkout.objects.all()):
    """Return an open checkout for given user if any."""
    return checkout_queryset.filter(user=user).first()


def get_or_create_checkout_from_request(request, checkout_queryset=Checkout.objects.all()):
    """Fetch checkout from database or create a new one based on cookie."""
    if request.user.is_authenticated:
        return get_or_create_user_checkout(request.user, checkout_queryset)[0]
    token = request.get_signed_cookie(COOKIE_NAME, default=None)
    return get_or_create_anonymous_checkout_from_token(token, checkout_queryset)


def get_checkout_from_request(request, checkout_queryset=Checkout.objects.all()):
    """Fetch checkout from database or return a new instance based on cookie."""
    if request.user.is_authenticated:
        checkout = get_user_checkout(request.user, checkout_queryset)
        user = request.user
    else:
        token = request.get_signed_cookie(COOKIE_NAME, default=None)
        checkout = get_anonymous_checkout_from_token(token, checkout_queryset)
        user = None
    if checkout is not None:
        return checkout
    if user:
        return Checkout(user=user)
    return Checkout()


def get_or_empty_db_checkout(checkout_queryset=Checkout.objects.all()):
    """Decorate view to receive a checkout if one exists.

    Changes the view signature from `func(request, ...)` to
    `func(request, checkout, ...)`.

    If no matching checkout is found, an unsaved `Checkout` instance will be used.
    """
    # FIXME: behave like middleware and assign checkout to request instead
    def get_checkout(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            checkout = get_checkout_from_request(request, checkout_queryset)
            return view(request, checkout, *args, **kwargs)
        return func
    return get_checkout


def find_open_checkout_for_user(user):
    """Find an open checkout for the given user."""
    checkouts = user.checkouts.all()
    open_checkout = checkouts.first()
    if len(checkouts) > 1:
        logger.warning('%s has more than one open basket', user)
        checkouts.exclude(token=open_checkout.token).delete()
    return open_checkout


def change_checkout_user(checkout, user):
    """Assign checkout to a user.

    If the user already has an open checkout assigned, cancel it.
    """
    open_checkout = find_open_checkout_for_user(user)
    if open_checkout is not None:
        open_checkout.delete()
    checkout.user = user
    checkout.shipping_address = user.default_shipping_address
    checkout.billing_address = user.default_billing_address
    checkout.save(update_fields=['user', 'shipping_address', 'billing_address'])


def update_checkout_quantity(checkout):
    """Update the total quantity in checkout."""
    total_lines = checkout.lines.aggregate(
        total_quantity=Sum('quantity'))['total_quantity']
    if not total_lines:
        total_lines = 0
    checkout.quantity = total_lines
    checkout.save(update_fields=['quantity'])


def add_variant_to_checkout(
        checkout, variant, quantity=1, replace=False, check_quantity=True):
    """Add a product variant to checkout.

    The `data` parameter may be used to differentiate between items with
    different customization options.

    If `replace` is truthy then any previous quantity is discarded instead
    of added to.
    """
    line, _ = checkout.lines.get_or_create(
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

    update_checkout_quantity(checkout)


def get_shipping_address_forms(checkout, user_addresses, data, country):
    """Forms initialized with data depending on shipping address in checkout."""
    shipping_address = (
        checkout.shipping_address or checkout.user.default_shipping_address)

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


def update_shipping_address_in_checkout(checkout, user_addresses, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, addresses_form, preview = (
        get_shipping_address_forms(checkout, user_addresses, data, country))

    updated = False

    if addresses_form.is_valid() and not preview:
        use_existing_address = (
            addresses_form.cleaned_data['address'] !=
            AddressChoiceForm.NEW_ADDRESS)

        if use_existing_address:
            address_id = addresses_form.cleaned_data['address']
            address = Address.objects.get(id=address_id)
            change_shipping_address_in_checkout(checkout, address)
            updated = True

        elif address_form.is_valid():
            address = address_form.save()
            change_shipping_address_in_checkout(checkout, address)
            updated = True

    return addresses_form, address_form, updated


def update_shipping_address_in_anonymous_checkout(checkout, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, preview = get_address_form(
        data, country_code=country.code,
        autocomplete_type='shipping',
        instance=checkout.shipping_address,
        initial={'country': country})
    user_form = AnonymousUserShippingForm(
        data if not preview else None, instance=checkout)

    updated = False

    if user_form.is_valid() and address_form.is_valid():
        user_form.save()
        address = address_form.save()
        change_shipping_address_in_checkout(checkout, address)
        updated = True

    return user_form, address_form, updated


def get_billing_forms_with_shipping(checkout, data, user_addresses, country):
    """Get billing form based on a the current billing and shipping data."""
    shipping_address = checkout.shipping_address
    billing_address = checkout.billing_address or Address(country=country)

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


def update_billing_address_in_checkout_with_shipping(
        checkout, user_addresses, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, addresses_form, preview = get_billing_forms_with_shipping(
        checkout, data, user_addresses, country)

    updated = False

    if addresses_form.is_valid() and not preview:
        address = None
        address_id = addresses_form.cleaned_data['address']

        if address_id == BillingAddressChoiceForm.SHIPPING_ADDRESS:
            if checkout.user and checkout.shipping_address in user_addresses:
                address = checkout.shipping_address
            else:
                address = checkout.shipping_address.get_copy()
        elif address_id != BillingAddressChoiceForm.NEW_ADDRESS:
            address = user_addresses.get(id=address_id)
        elif address_form.is_valid():
            address = address_form.save()

        if address:
            change_billing_address_in_checkout(checkout, address)
            updated = True

    return addresses_form, address_form, updated


def get_anonymous_summary_without_shipping_forms(checkout, data, country):
    """Forms initialized with data depending on addresses in checkout."""
    billing_address = checkout.billing_address

    if billing_address:
        address_form, preview = get_address_form(
            data, country_code=billing_address.country.code,
            autocomplete_type='billing', instance=billing_address)
    else:
        address_form, preview = get_address_form(
            data, country_code=country.code,
            autocomplete_type='billing', initial={'country': country})

    return address_form, preview


def update_billing_address_in_anonymous_checkout(checkout, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, preview = get_anonymous_summary_without_shipping_forms(
        checkout, data, country)
    user_form = AnonymousUserBillingForm(data, instance=checkout)

    updated = False

    if user_form.is_valid() and address_form.is_valid() and not preview:
        user_form.save()
        address = address_form.save()
        change_billing_address_in_checkout(checkout, address)
        updated = True

    return user_form, address_form, updated


def get_summary_without_shipping_forms(checkout, user_addresses, data, country):
    """Forms initialized with data depending on addresses in checkout."""
    billing_address = checkout.billing_address

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
        if checkout.user and checkout.user.default_billing_address:
            initial_address = checkout.user.default_billing_address.id
        else:
            initial_address = AddressChoiceForm.NEW_ADDRESS

    addresses_form = AddressChoiceForm(
        data, addresses=user_addresses, initial={'address': initial_address})
    return address_form, addresses_form, preview


def update_billing_address_in_checkout(checkout, user_addresses, data, country):
    """Return shipping address choice forms and if an address was updated."""
    address_form, addresses_form, preview = (
        get_summary_without_shipping_forms(
            checkout, user_addresses, data, country))

    updated = False

    if addresses_form.is_valid():
        use_existing_address = (
            addresses_form.cleaned_data['address'] !=
            AddressChoiceForm.NEW_ADDRESS)

        if use_existing_address:
            address_id = addresses_form.cleaned_data['address']
            address = Address.objects.get(id=address_id)
            change_billing_address_in_checkout(checkout, address)
            updated = True

        elif address_form.is_valid():
            address = address_form.save()
            change_billing_address_in_checkout(checkout, address)
            updated = True

    return addresses_form, address_form, updated


def _check_new_checkout_address(checkout, address, address_type):
    """Check if and address in checkout has changed and if to remove old one."""
    if address_type == AddressType.BILLING:
        old_address = checkout.billing_address
    else:
        old_address = checkout.shipping_address

    has_address_changed = any([
        not address and old_address,
        address and not old_address,
        address and old_address and address != old_address])

    remove_old_address = (
        has_address_changed and
        old_address is not None and
        (not checkout.user or old_address not in checkout.user.addresses.all()))

    return has_address_changed, remove_old_address


def change_billing_address_in_checkout(checkout, address):
    """Save billing address in checkout if changed.

    Remove previously saved address if not connected to any user.
    """
    changed, remove = _check_new_checkout_address(
        checkout, address, AddressType.BILLING)
    if changed:
        if remove:
            checkout.billing_address.delete()
        checkout.billing_address = address
        checkout.save(update_fields=['billing_address'])


def change_shipping_address_in_checkout(checkout, address):
    """Save shipping address in checkout if changed.

    Remove previously saved address if not connected to any user.
    """
    changed, remove = _check_new_checkout_address(
        checkout, address, AddressType.SHIPPING)
    if changed:
        if remove:
            checkout.shipping_address.delete()
        checkout.shipping_address = address
        checkout.save(update_fields=['shipping_address'])


def get_checkout_context(checkout, discounts, taxes, currency=None, shipping_range=None):
    """Data shared between views in checkout process."""
    checkout_total = checkout.get_total(discounts, taxes)
    checkout_subtotal = checkout.get_subtotal(discounts, taxes)
    shipping_required = checkout.is_shipping_required()
    checkout_subtotal = checkout.get_subtotal(discounts, taxes)
    total_with_shipping = TaxedMoneyRange(
        start=checkout_subtotal, stop=checkout_subtotal)
    if shipping_required and shipping_range:
        total_with_shipping = shipping_range + checkout_subtotal

    context = {
        'checkout': checkout,
        'checkout_are_taxes_handled': bool(taxes),
        'checkout_lines': [
            (line, line.get_total(discounts, taxes)) for line in checkout],
        'checkout_shipping_price': checkout.get_shipping_price(taxes),
        'checkout_subtotal': checkout_subtotal,
        'checkout_total': checkout_total,
        'shipping_required': checkout.is_shipping_required(),
        'total_with_shipping': total_with_shipping}

    if currency:
        context.update(
            local_checkout_total=to_local_currency(
                checkout_total, currency),
            local_checkout_subtotal=to_local_currency(
                checkout_subtotal, currency),
            local_total_with_shipping=to_local_currency(
                total_with_shipping, currency))

    return context


def _get_shipping_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value for a voucher of shipping type."""
    if not checkout.is_shipping_required():
        msg = pgettext(
            'Voucher not applicable',
            'Your order does not require shipping.')
        raise NotApplicable(msg)
    shipping_method = checkout.shipping_method
    if not shipping_method:
        msg = pgettext(
            'Voucher not applicable',
            'Please select a shipping method first.')
        raise NotApplicable(msg)

    # check if voucher is limited to specified countries
    shipping_country = checkout.shipping_address.country
    if voucher.countries and shipping_country.code not in voucher.countries:
        msg = pgettext(
            'Voucher not applicable',
            'This offer is not valid in your country.')
        raise NotApplicable(msg)

    return get_shipping_voucher_discount(
        voucher, checkout.get_subtotal(), shipping_method.get_total())


def _get_products_voucher_discount(order_or_checkout, voucher):
    """Calculate products discount value for a voucher, depending on its type.
    """
    if voucher.type == VoucherType.PRODUCT:
        prices = get_prices_of_discounted_products(
            order_or_checkout.lines.all(), voucher.products.all())
    elif voucher.type == VoucherType.COLLECTION:
        prices = get_prices_of_products_in_discounted_collections(
            order_or_checkout.lines.all(), voucher.collections.all())
    elif voucher.type == VoucherType.CATEGORY:
        prices = get_prices_of_products_in_discounted_categories(
            order_or_checkout.lines.all(), voucher.categories.all())
    if not prices:
        msg = pgettext(
            'Voucher not applicable',
            'This offer is only valid for selected items.')
        raise NotApplicable(msg)
    return get_products_voucher_discount(voucher, prices)


def get_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    if voucher.type == VoucherType.VALUE:
        return get_value_voucher_discount(voucher, checkout.get_subtotal())
    if voucher.type == VoucherType.SHIPPING:
        return _get_shipping_voucher_discount_for_checkout(voucher, checkout)
    if voucher.type in (
            VoucherType.PRODUCT, VoucherType.COLLECTION, VoucherType.CATEGORY):
        return _get_products_voucher_discount(checkout, voucher)
    raise NotImplementedError('Unknown discount type')


def get_voucher_for_checkout(checkout, vouchers=None):
    """Return voucher with voucher code saved in checkout if active or None."""
    if checkout.voucher_code is not None:
        if vouchers is None:
            vouchers = Voucher.objects.active(date=date.today())
        try:
            return vouchers.get(code=checkout.voucher_code)
        except Voucher.DoesNotExist:
            return None
    return None


def recalculate_checkout_discount(checkout, discounts, taxes):
    """Recalculate `checkout.discount` based on the voucher.

    Will clear both voucher and discount if the discount is no longer
    applicable.
    """
    voucher = get_voucher_for_checkout(checkout)
    if voucher is not None:
        try:
            discount = get_voucher_discount_for_checkout(voucher, checkout)
        except NotApplicable:
            remove_voucher_from_checkout(checkout)
        else:
            subtotal = checkout.get_subtotal(discounts, taxes).gross
            checkout.discount_amount = min(discount, subtotal)
            checkout.discount_name = str(voucher)
            checkout.translated_discount_name = (
                voucher.translated.name
                if voucher.translated.name != voucher.name else '')
            checkout.save(
                update_fields=[
                    'translated_discount_name',
                    'discount_amount', 'discount_name'])
    else:
        remove_voucher_from_checkout(checkout)


def add_voucher_to_checkout(voucher, checkout):
    """Add voucher data to checkout.

    Raise NotApplicable if voucher of given type cannot be applied."""
    discount_amount = get_voucher_discount_for_checkout(voucher, checkout)
    checkout.voucher_code = voucher.code
    checkout.discount_name = voucher.name
    checkout.translated_discount_name = (
        voucher.translated.name
        if voucher.translated.name != voucher.name else '')
    checkout.discount_amount = discount_amount
    checkout.save(
        update_fields=[
            'voucher_code', 'discount_name', 'translated_discount_name',
            'discount_amount'])


def remove_voucher_from_checkout(checkout):
    """Remove voucher data from checkout."""
    checkout.voucher_code = None
    checkout.discount_name = None
    checkout.translated_discount_name = None
    checkout.discount_amount = ZERO_MONEY
    checkout.save(
        update_fields=[
            'voucher_code', 'discount_name', 'translated_discount_name',
            'discount_amount'])


def get_taxes_for_checkout(checkout, default_taxes):
    """Return taxes (if handled) due to shipping address or default one."""
    if not settings.VATLAYER_ACCESS_KEY:
        return None

    if checkout.shipping_address:
        return get_taxes_for_country(checkout.shipping_address.country)

    return default_taxes


def is_valid_shipping_method(checkout, taxes, discounts):
    """Check if shipping method is valid and remove (if not)."""
    if not checkout.shipping_method:
        return False

    valid_methods = ShippingMethod.objects.applicable_shipping_methods(
        price=checkout.get_subtotal(discounts, taxes).gross,
        weight=checkout.get_total_weight(),
        country_code=checkout.shipping_address.country.code)
    if checkout.shipping_method not in valid_methods:
        clear_shipping_method(checkout)
        return False
    return True


def clear_shipping_method(checkout):
    checkout.shipping_method = None
    checkout.save(update_fields=['shipping_method'])


def _process_voucher_data_for_order(checkout):
    """Fetch, process and return voucher/discount data from checkout."""
    vouchers = Voucher.objects.active(date=date.today()).select_for_update()
    voucher = get_voucher_for_checkout(checkout, vouchers)

    if checkout.voucher_code and not voucher:
        msg = pgettext(
            'Voucher not applicable',
            'Voucher expired in meantime. Order placement aborted.')
        raise NotApplicable(msg)

    if not voucher:
        return {}

    increase_voucher_usage(voucher)
    return {
        'voucher': voucher,
        'discount_amount': checkout.discount_amount,
        'discount_name': checkout.discount_name,
        'translated_discount_name': checkout.translated_discount_name}


def _process_shipping_data_for_order(checkout, taxes):
    """Fetch, process and return shipping data from checkout."""
    if not checkout.is_shipping_required():
        return {}

    shipping_address = checkout.shipping_address

    if checkout.user:
        store_user_address(checkout.user, shipping_address, AddressType.SHIPPING)
        if checkout.user.addresses.filter(pk=shipping_address.pk).exists():
            shipping_address = shipping_address.get_copy()

    return {
        'shipping_address': shipping_address,
        'shipping_method': checkout.shipping_method,
        'shipping_method_name': smart_text(checkout.shipping_method),
        'shipping_price': checkout.get_shipping_price(taxes),
        'weight': checkout.get_total_weight()}


def _process_user_data_for_order(checkout):
    """Fetch, process and return shipping data from checkout."""
    billing_address = checkout.billing_address

    if checkout.user:
        store_user_address(checkout.user, billing_address, AddressType.BILLING)
        if checkout.user.addresses.filter(pk=billing_address.pk).exists():
            billing_address = billing_address.get_copy()

    return {
        'user': checkout.user,
        'user_email': checkout.user.email if checkout.user else checkout.email,
        'billing_address': billing_address,
        'customer_note': checkout.note}


@transaction.atomic
def create_order(checkout: Checkout, tracking_code: str, discounts, taxes):
    """Create an order from the checkout.

    Each order will get a private copy of both the billing and the shipping
    address (if shipping).

    If any of the addresses is new and the user is logged in the address
    will also get saved to that user's address book.

    Current user's language is saved in the order so we can later determine
    which language to use when sending email.
    """
    from ..order.utils import add_variant_to_order

    order = Order.objects.filter(checkout_token=checkout.token).first()
    if order is not None:
        return order

    order_data = {}
    order_data.update(_process_voucher_data_for_order(checkout))
    order_data.update(_process_shipping_data_for_order(checkout, taxes))
    order_data.update(_process_user_data_for_order(checkout))
    order_data.update({
        'language_code': get_language(),
        'tracking_client_id': tracking_code,
        'total': checkout.get_total(discounts, taxes)})

    order = Order.objects.create(**order_data, checkout_token=checkout.token)

    # create order lines from checkout lines
    for line in checkout:
        add_variant_to_order(
            order, line.variant, line.quantity, discounts, taxes)

    # assign checkout payments to the order
    checkout.payments.update(order=order)
    return order


def is_fully_paid(checkout: Checkout, taxes, discounts):
    """Check if provided payment methods cover the checkout's total amount.
    Note that these payments may not be captured or charged at all."""
    payments = [
        payment for payment in checkout.payments.all() if payment.is_active]
    total_paid = sum([p.total for p in payments])
    checkout_total = checkout.get_total(discounts=discounts, taxes=taxes).gross.amount
    return total_paid >= checkout_total


def clean_checkout(checkout: Checkout, taxes, discounts):
    """Check if checkout can be completed."""
    if checkout.is_shipping_required():
        if not checkout.shipping_method:
            raise ValidationError('Shipping method is not set')
        if not checkout.shipping_address:
            raise ValidationError('Shipping address is not set')
        if not is_valid_shipping_method(checkout, taxes, discounts):
            raise ValidationError(
                'Shipping method is not valid for your shipping address')

    if not checkout.billing_address:
        raise ValidationError('Billing address is not set')

    if not is_fully_paid(checkout, taxes, discounts):
        raise ValidationError(
            'Provided payment methods can not cover the checkout\'s total '
            'amount')
