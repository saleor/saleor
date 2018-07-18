"""Cart and checkout related views."""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse

from ...account.forms import LoginForm
from ...core.utils import (
    format_money, get_user_shipping_country, to_local_currency)
from ...product.models import ProductVariant
from ...shipping.utils import get_shipment_options
from ..forms import CartShippingMethodForm, CountryForm, ReplaceCartLineForm
from ..models import Cart
from ..utils import (
    check_product_availability_and_warn, check_shipping_method, get_cart_data,
    get_cart_data_for_checkout, get_or_empty_db_cart, get_taxes_for_cart)
from .discount import add_voucher_form, validate_voucher
from .shipping import (
    anonymous_user_shipping_address_view, user_shipping_address_view)
from .summary import (
    anonymous_summary_without_shipping, summary_with_shipping_view,
    summary_without_shipping)
from .validators import (
    validate_cart, validate_is_shipping_required, validate_shipping_address,
    validate_shipping_method)


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_cart
def checkout_login(request, cart):
    """Allow the user to log in prior to checkout."""
    if request.user.is_authenticated:
        return redirect('checkout:index')
    ctx = {'form': LoginForm()}
    return TemplateResponse(request, 'checkout/login.html', ctx)


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_cart
@validate_is_shipping_required
def checkout_index(request, cart):
    """Redirect to the initial step of checkout."""
    return redirect('checkout:shipping-address')


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_voucher
@validate_cart
@validate_is_shipping_required
@add_voucher_form
def checkout_shipping_address(request, cart):
    """Display the correct shipping address step."""
    if request.user.is_authenticated:
        return user_shipping_address_view(request, cart)
    return anonymous_user_shipping_address_view(request, cart)


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_voucher
@validate_cart
@validate_is_shipping_required
@validate_shipping_address
@add_voucher_form
def checkout_shipping_method(request, cart):
    """Display the shipping method selection step."""
    taxes = get_taxes_for_cart(cart, request.taxes)
    check_shipping_method(cart)
    form = CartShippingMethodForm(
        request.POST or None, taxes=taxes, instance=cart,
        initial={'shipping_method': cart.shipping_method})

    if form.is_valid():
        form.save()
        return redirect('checkout:summary')

    ctx = get_cart_data_for_checkout(cart, request.discounts, taxes)
    ctx.update({'shipping_method_form': form})
    return TemplateResponse(request, 'checkout/shipping_method.html', ctx)


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_voucher
@validate_cart
@add_voucher_form
def checkout_summary(request, cart):
    """Display the correct order summary."""
    if cart.is_shipping_required():
        view = validate_shipping_method(summary_with_shipping_view)
        view = validate_shipping_address(view)
        return view(request, cart)
    if request.user.is_authenticated:
        return summary_without_shipping(request, cart)
    return anonymous_summary_without_shipping(request, cart)


@get_or_empty_db_cart(cart_queryset=Cart.objects.for_display())
def cart_index(request, cart):
    """Display cart details."""
    discounts = request.discounts
    taxes = request.taxes
    cart_lines = []
    check_product_availability_and_warn(request, cart)

    # refresh required to get updated cart lines and it's quantity
    try:
        cart = Cart.objects.prefetch_related(
            'lines__variant__product__category').get(pk=cart.pk)
    except Cart.DoesNotExist:
        pass

    lines = cart.lines.select_related(
        'variant__product__product_type',
        'variant__product__category')
    lines = lines.prefetch_related(
        'variant__product__collections',
        'variant__product__images',
        'variant__product__product_type__variant_attributes')
    for line in lines:
        initial = {'quantity': line.quantity}
        form = ReplaceCartLineForm(
            None, cart=cart, variant=line.variant, initial=initial,
            discounts=discounts, taxes=taxes)
        cart_lines.append({
            'variant': line.variant,
            'get_price': line.variant.get_price(discounts, taxes),
            'get_total': line.get_total(discounts, taxes),
            'form': form})

    default_country = get_user_shipping_country(request)
    country_form = CountryForm(initial={'country': default_country})
    default_country_options = get_shipment_options(default_country, taxes)

    cart_data = get_cart_data(
        cart, default_country_options, request.currency, discounts, taxes)
    ctx = {
        'cart_lines': cart_lines,
        'country_form': country_form,
        'default_country_options': default_country_options}
    ctx.update(cart_data)

    return TemplateResponse(request, 'checkout/index.html', ctx)


@get_or_empty_db_cart(cart_queryset=Cart.objects.for_display())
def cart_shipping_options(request, cart):
    """Display shipping options to get a price estimate."""
    country_form = CountryForm(request.POST or None, taxes=request.taxes)
    if country_form.is_valid():
        shipments = country_form.get_shipment_options()
    else:
        shipments = None
    ctx = {
        'default_country_options': shipments,
        'country_form': country_form}
    cart_data = get_cart_data(
        cart, shipments, request.currency, request.discounts, request.taxes)
    ctx.update(cart_data)
    return TemplateResponse(request, 'checkout/_subtotal_table.html', ctx)


@get_or_empty_db_cart()
def update_cart_line(request, cart, variant_id):
    """Update the line quantities."""
    if not request.is_ajax():
        return redirect('cart:index')
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    discounts = request.discounts
    taxes = request.taxes
    status = None
    form = ReplaceCartLineForm(
        request.POST, cart=cart, variant=variant, discounts=discounts,
        taxes=taxes)
    if form.is_valid():
        form.save()
        response = {
            'variantId': variant_id,
            'subtotal': 0,
            'total': 0,
            'cart': {
                'numItems': cart.quantity,
                'numLines': len(cart)}}
        updated_line = cart.get_line(form.cart_line.variant)
        if updated_line:
            response['subtotal'] = format_money(
                updated_line.get_total(discounts, taxes).gross)
        if cart:
            cart_total = cart.get_subtotal(discounts, taxes)
            response['total'] = format_money(cart_total.gross)
            local_cart_total = to_local_currency(cart_total, request.currency)
            if local_cart_total is not None:
                response['localTotal'] = format_money(local_cart_total.gross)
        status = 200
    elif request.POST is not None:
        response = {'error': form.errors}
        status = 400
    return JsonResponse(response, status=status)


@get_or_empty_db_cart(cart_queryset=Cart.objects.for_display())
def cart_summary(request, cart):
    """Display a cart summary suitable for displaying on all pages."""
    discounts = request.discounts
    taxes = request.taxes

    def prepare_line_data(line):
        first_image = line.variant.get_first_image()
        return {
            'product': line.variant.product,
            'variant': line.variant.name,
            'quantity': line.quantity,
            'image': first_image,
            'line_total': line.get_total(discounts, taxes),
            'variant_url': line.variant.get_absolute_url()}

    if cart.quantity == 0:
        data = {'quantity': 0}
    else:
        data = {
            'quantity': cart.quantity,
            'total': cart.get_subtotal(discounts, taxes),
            'lines': [prepare_line_data(line) for line in cart]}

    return render(request, 'cart_dropdown.html', data)
