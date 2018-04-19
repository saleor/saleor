"""Cart-related views."""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse

from ..core.utils import (
    format_money, get_user_shipping_country, to_local_currency)
from ..product.models import ProductVariant
from ..shipping.utils import get_shipment_options
from .forms import CountryForm, ReplaceCartLineForm
from .models import Cart
from .utils import (
    check_product_availability_and_warn, get_cart_data, get_or_empty_db_cart)


@get_or_empty_db_cart(cart_queryset=Cart.objects.for_display())
def index(request, cart):
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
    default_country_options = get_shipment_options(
        default_country, request.taxes)

    cart_data = get_cart_data(
        cart, default_country_options, request.currency, discounts, taxes)
    ctx = {
        'cart_lines': cart_lines,
        'country_form': country_form,
        'default_country_options': default_country_options}
    ctx.update(cart_data)

    return TemplateResponse(
        request, 'cart/index.html', ctx)


@get_or_empty_db_cart(cart_queryset=Cart.objects.for_display())
def get_shipping_options(request, cart):
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
    return TemplateResponse(
        request, 'cart/_subtotal_table.html', ctx)


@get_or_empty_db_cart()
def update(request, cart, variant_id):
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
            cart_total = cart.get_total(discounts, taxes)
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
def summary(request, cart):
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
            'total': cart.get_total(discounts, taxes),
            'lines': [prepare_line_data(line) for line in cart.lines.all()]}

    return render(request, 'cart_dropdown.html', data)
