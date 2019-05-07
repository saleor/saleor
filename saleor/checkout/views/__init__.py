"""Checkout related views."""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse

from ...account.forms import LoginForm
from ...core.utils import (
    format_money, get_user_shipping_country, to_local_currency)
from ...shipping.utils import get_shipping_price_estimate
from ..forms import (
    CheckoutShippingMethodForm, CountryForm, ReplaceCheckoutLineForm)
from ..models import Checkout
from ..utils import (
    check_product_availability_and_warn, get_checkout_context,
    get_or_empty_db_checkout, get_taxes_for_checkout, is_valid_shipping_method,
    update_checkout_quantity)
from .discount import add_voucher_form, validate_voucher
from .shipping import (
    anonymous_user_shipping_address_view, user_shipping_address_view)
from .summary import (
    anonymous_summary_without_shipping, summary_with_shipping_view,
    summary_without_shipping)
from .validators import (
    validate_checkout, validate_is_shipping_required,
    validate_shipping_address, validate_shipping_method)


@get_or_empty_db_checkout(Checkout.objects.for_display())
@validate_checkout
def checkout_login(request, checkout):
    """Allow the user to log in prior to checkout."""
    if request.user.is_authenticated:
        return redirect('checkout:start')
    ctx = {'form': LoginForm()}
    return TemplateResponse(request, 'checkout/login.html', ctx)


@get_or_empty_db_checkout(Checkout.objects.for_display())
@validate_checkout
@validate_is_shipping_required
def checkout_start(request, checkout):
    """Redirect to the initial step of checkout."""
    return redirect('checkout:shipping-address')


@get_or_empty_db_checkout(Checkout.objects.for_display())
@validate_voucher
@validate_checkout
@validate_is_shipping_required
@add_voucher_form
def checkout_shipping_address(request, checkout):
    """Display the correct shipping address step."""
    if request.user.is_authenticated:
        return user_shipping_address_view(request, checkout)
    return anonymous_user_shipping_address_view(request, checkout)


@get_or_empty_db_checkout(Checkout.objects.for_display())
@validate_voucher
@validate_checkout
@validate_is_shipping_required
@validate_shipping_address
@add_voucher_form
def checkout_shipping_method(request, checkout):
    """Display the shipping method selection step."""
    discounts = request.discounts
    taxes = get_taxes_for_checkout(checkout, request.taxes)
    is_valid_shipping_method(checkout, request.taxes, discounts)

    form = CheckoutShippingMethodForm(
        request.POST or None, discounts=discounts, taxes=taxes, instance=checkout,
        initial={'shipping_method': checkout.shipping_method})
    if form.is_valid():
        form.save()
        return redirect('checkout:summary')

    ctx = get_checkout_context(checkout, discounts, taxes)
    ctx.update({'shipping_method_form': form})
    return TemplateResponse(request, 'checkout/shipping_method.html', ctx)


@get_or_empty_db_checkout(Checkout.objects.for_display())
@validate_voucher
@validate_checkout
@add_voucher_form
def checkout_order_summary(request, checkout):
    """Display the correct order summary."""
    if checkout.is_shipping_required():
        view = validate_shipping_method(summary_with_shipping_view)
        view = validate_shipping_address(view)
        return view(request, checkout)
    if request.user.is_authenticated:
        return summary_without_shipping(request, checkout)
    return anonymous_summary_without_shipping(request, checkout)


@get_or_empty_db_checkout(checkout_queryset=Checkout.objects.for_display())
def checkout_index(request, checkout):
    """Display checkout details."""
    discounts = request.discounts
    taxes = request.taxes
    checkout_lines = []
    check_product_availability_and_warn(request, checkout)

    # refresh required to get updated checkout lines and it's quantity
    try:
        checkout = Checkout.objects.prefetch_related(
            'lines__variant__product__category').get(pk=checkout.pk)
    except Checkout.DoesNotExist:
        pass

    lines = checkout.lines.select_related('variant__product__product_type')
    lines = lines.prefetch_related(
        'variant__translations', 'variant__product__translations',
        'variant__product__images',
        'variant__product__product_type__variant_attributes__translations',
        'variant__images',
        'variant__product__product_type__variant_attributes')
    for line in lines:
        initial = {'quantity': line.quantity}
        form = ReplaceCheckoutLineForm(
            None, checkout=checkout, variant=line.variant, initial=initial,
            discounts=discounts, taxes=taxes)
        checkout_lines.append({
            'variant': line.variant,
            'get_price': line.variant.get_price(discounts, taxes),
            'get_total': line.get_total(discounts, taxes),
            'form': form})

    default_country = get_user_shipping_country(request)
    country_form = CountryForm(initial={'country': default_country})
    shipping_price_range = get_shipping_price_estimate(
        price=checkout.get_subtotal(discounts, taxes).gross,
        weight=checkout.get_total_weight(), country_code=default_country,
        taxes=taxes)

    context = get_checkout_context(
        checkout, discounts, taxes,
        currency=request.currency, shipping_range=shipping_price_range)
    context.update({
        'checkout_lines': checkout_lines,
        'country_form': country_form,
        'shipping_price_range': shipping_price_range})

    return TemplateResponse(request, 'checkout/index.html', context)


@get_or_empty_db_checkout(checkout_queryset=Checkout.objects.for_display())
def checkout_shipping_options(request, checkout):
    """Display shipping options to get a price estimate."""
    country_form = CountryForm(request.POST or None, taxes=request.taxes)
    if country_form.is_valid():
        shipping_price_range = country_form.get_shipping_price_estimate(
            price=checkout.get_subtotal(request.discounts, request.taxes).gross,
            weight=checkout.get_total_weight())
    else:
        shipping_price_range = None
    ctx = {
        'shipping_price_range': shipping_price_range,
        'country_form': country_form}
    checkout_data = get_checkout_context(
        checkout, request.discounts,request.taxes,
        currency=request.currency, shipping_range=shipping_price_range)
    ctx.update(checkout_data)
    return TemplateResponse(request, 'checkout/_subtotal_table.html', ctx)


@get_or_empty_db_checkout(
    Checkout.objects.prefetch_related('lines__variant__product'))
def update_checkout_line(request, checkout, variant_id):
    """Update the line quantities."""
    if not request.is_ajax():
        return redirect('checkout:index')

    checkout_line = get_object_or_404(checkout.lines, variant_id=variant_id)
    discounts = request.discounts
    taxes = request.taxes
    status = None
    form = ReplaceCheckoutLineForm(
        request.POST,
        checkout=checkout,
        variant=checkout_line.variant,
        discounts=discounts,
        taxes=taxes)
    if form.is_valid():
        form.save()
        response = {
            'variantId': variant_id,
            'subtotal': format_money(
                checkout_line.get_total(discounts, taxes).gross),
            'total': 0,
            'checkout': {
                'numItems': checkout.quantity,
                'numLines': len(checkout)}}

        checkout_total = checkout.get_subtotal(discounts, taxes)
        response['total'] = format_money(checkout_total.gross)
        local_checkout_total = to_local_currency(
            checkout_total, request.currency)
        if local_checkout_total is not None:
            response['localTotal'] = format_money(local_checkout_total.gross)

        status = 200
    elif request.POST is not None:
        response = {'error': form.errors}
        status = 400
    return JsonResponse(response, status=status)


@get_or_empty_db_checkout()
def clear_checkout(request, checkout):
    """Clear checkout."""
    if not request.is_ajax():
        return redirect('checkout:index')
    checkout.lines.all().delete()
    update_checkout_quantity(checkout)
    response = {'numItems': 0}
    return JsonResponse(response)


@get_or_empty_db_checkout(checkout_queryset=Checkout.objects.for_display())
def checkout_dropdown(request, checkout):
    """Display a checkout summary suitable for displaying on all pages."""
    discounts = request.discounts
    taxes = request.taxes

    def prepare_line_data(line):
        first_image = line.variant.get_first_image()
        if first_image:
            first_image = first_image.image
        return {
            'product': line.variant.product,
            'variant': line.variant,
            'quantity': line.quantity,
            'image': first_image,
            'line_total': line.get_total(discounts, taxes),
            'variant_url': line.variant.get_absolute_url()}

    if checkout.quantity == 0:
        data = {'quantity': 0}
    else:
        data = {
            'quantity': checkout.quantity,
            'total': checkout.get_subtotal(discounts, taxes),
            'lines': [prepare_line_data(line) for line in checkout]}

    return render(request, 'checkout_dropdown.html', data)
