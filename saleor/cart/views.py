from __future__ import unicode_literals

from babeldjango.templatetags.babel import currencyfmt
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse

from ..core.utils import to_local_currency, get_user_shipping_country
from ..product.models import ProductVariant
from ..shipping.utils import get_shipment_options
from .forms import ReplaceCartLineForm, CountryForm
from .models import Cart
from .utils import check_product_availability_and_warn, get_or_empty_db_cart


@get_or_empty_db_cart(cart_queryset=Cart.objects.for_display())
def index(request, cart):
    discounts = request.discounts
    country = request.country
    cart_lines = []
    check_product_availability_and_warn(request, cart)

    for line in cart.lines.all():
        initial = {'quantity': line.get_quantity()}
        form = ReplaceCartLineForm(None, cart=cart, variant=line.variant,
                                   initial=initial, discounts=discounts)
        cart_lines.append({
            'variant': line.variant,
            'get_price_per_item': line.get_price_per_item(
                discounts, country=country),
            'get_total': line.get_total(discounts=discounts, country=country),
            'form': form})

    cart_total = None
    local_cart_total = None
    if cart:
        cart_total = cart.get_total(discounts=discounts, country=country)
        local_cart_total = to_local_currency(cart_total, request.currency)

    default_country = get_user_shipping_country(request)
    country_form = CountryForm(initial={'country': default_country})
    default_country_options = get_shipment_options(default_country)

    return TemplateResponse(
        request, 'cart/index.html',
        {
            'cart_lines': cart_lines,
            'cart_total': cart_total,
            'local_cart_total': local_cart_total,
            'country_form': country_form,
            'default_country_options': default_country_options})


def get_shipping_options(request):
    country_form = CountryForm(request.POST or None)
    if country_form.is_valid():
        shipments = country_form.get_shipment_options()
        return JsonResponse({'options': list(shipments)})


@get_or_empty_db_cart()
def update(request, cart, variant_id):
    if not request.is_ajax():
        return redirect('cart:index')
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    discounts = request.discounts
    status = None
    form = ReplaceCartLineForm(request.POST, cart=cart, variant=variant,
                               discounts=discounts)
    if form.is_valid():
        form.save()
        response = {'variantId': variant_id,
                    'subtotal': 0,
                    'total': 0,
                    'cart': {
                        'numItems': cart.quantity,
                        'numLines': len(cart)
                    }}
        updated_line = cart.get_line(form.cart_line.variant)
        if updated_line:
            country = request.country
            response['subtotal'] = currencyfmt(
                updated_line.get_total(
                    discounts=discounts, country=country).gross,
                updated_line.get_total(
                    discounts=discounts, country=country).currency)
        if cart:
            cart_total = cart.get_total(discounts=discounts, country=country)
            response['total'] = currencyfmt(
                cart_total.gross,
                cart_total.currency)
            local_cart_total = to_local_currency(cart_total, request.currency)
            if local_cart_total:
                response['localTotal'] = currencyfmt(
                    local_cart_total.gross,
                    local_cart_total.currency)
        status = 200
    elif request.POST is not None:
        response = {'error': form.errors}
        status = 400
    return JsonResponse(response, status=status)


@get_or_empty_db_cart(cart_queryset=Cart.objects.for_display())
def summary(request, cart):

    def prepare_line_data(line):
        country = request.country
        product_class = line.variant.product.product_class
        attributes = product_class.variant_attributes.all()
        first_image = line.variant.get_first_image()
        price_per_item = line.get_price_per_item(
            discounts=request.discounts, country=country)
        line_total = line.get_total(discounts=request.discounts,
                                    country=country)
        return {
            'product': line.variant.product,
            'variant': line.variant.name,
            'quantity': line.quantity,
            'attributes': line.variant.display_variant(attributes),
            'image': first_image,
            'price_per_item': currencyfmt(
                price_per_item.gross, price_per_item.currency),
            'line_total': currencyfmt(line_total.gross, line_total.currency),
            'update_url': reverse('cart:update-line',
                                  kwargs={'variant_id': line.variant_id}),
            'variant_url': line.variant.get_absolute_url()}
    if cart.quantity == 0:
        data = {'quantity': 0}
    else:
        cart_total = cart.get_total(discounts=request.discounts,
                                    country=request.country)
        data = {
            'quantity': cart.quantity,
            'total': currencyfmt(cart_total.gross, cart_total.currency),
            'lines': [prepare_line_data(line) for line in cart.lines.all()]}

    return render(request, 'cart-dropdown.html', data)
