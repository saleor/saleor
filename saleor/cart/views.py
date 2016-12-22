from __future__ import unicode_literals

from allauth.utils import get_request_param
from babeldjango.templatetags.babel import currencyfmt
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from ..core.utils import to_local_currency
from ..product.models import ProductVariant
from .forms import ReplaceCartLineForm
from .models import Cart
from .utils import (check_product_availability_and_warn,
                    find_and_assign_anonymous_cart, get_or_create_db_cart,
                    get_or_empty_db_cart)


@get_or_empty_db_cart(cart_queryset=Cart.objects.for_display())
def index(request, cart):
    discounts = request.discounts
    cart_lines = []
    check_product_availability_and_warn(request, cart)

    for line in cart.lines.all():
        initial = {'quantity': line.get_quantity()}
        form = ReplaceCartLineForm(None, cart=cart, variant=line.variant,
                                   initial=initial, discounts=discounts)
        cart_lines.append({
            'variant': line.variant,
            'get_price_per_item': line.get_price_per_item(discounts),
            'get_total': line.get_total(discounts=discounts),
            'form': form})

    cart_total = None
    local_cart_total = None
    if cart:
        cart_total = cart.get_total(discounts=discounts)
        local_cart_total = to_local_currency(cart_total, request.currency)

    return TemplateResponse(
        request, 'cart/index.html',
        {
            'cart_lines': cart_lines,
            'cart_total': cart_total,
            'local_cart_total': local_cart_total})


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
        response = {'productId': variant_id,
                    'subtotal': 0,
                    'total': 0}
        updated_line = cart.get_line(form.cart_line.variant)
        if updated_line:
            response['subtotal'] = currencyfmt(
                updated_line.get_total(discounts=discounts).gross,
                updated_line.get_total(discounts=discounts).currency)
        if cart:
            cart_total = cart.get_total(discounts=discounts)
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
        product_class = line.variant.product.product_class
        attributes = product_class.variant_attributes.all()
        first_image = line.variant.get_first_image()
        price_per_item = line.get_price_per_item(discounts=request.discounts)
        line_total = line.get_total(discounts=request.discounts)
        return {
            'variant': line.variant.name,
            'quantity': line.quantity,
            'attributes': line.variant.display_variant(attributes),
            'image': first_image.url if first_image else None,
            'price_per_item': currencyfmt(
                price_per_item.gross, price_per_item.currency),
            'line_total': currencyfmt(line_total.gross, line_total.currency),
            'update_url': reverse('cart:update-line',
                                  kwargs={'variant_id': line.variant_id}),
            'variant_url': line.variant.get_absolute_url()}
    if cart.quantity == 0:
        data = {}
    else:
        cart_total = cart.get_total(discounts=request.discounts)
        data = {
            'quantity': cart.quantity,
            'total': currencyfmt(cart_total.gross, cart_total.currency),
            'lines': [prepare_line_data(line) for line in cart.lines.all()]}

    return JsonResponse(data)


def assign_cart_and_redirect_view(request):
    find_and_assign_anonymous_cart(request)
    redirect_to = get_request_param(request, "next")
    if redirect_to is None:
        redirect_to = '/'
    response = HttpResponseRedirect(redirect_to)
    response.delete_cookie(Cart.COOKIE_NAME)
    return response
