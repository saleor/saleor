"""Checkout related views."""
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse

from ...account.forms import LoginForm
from ...core.taxes import get_display_price, quantize_price, zero_taxed_money
from ...core.utils import format_money, get_user_shipping_country, to_local_currency
from ..forms import CheckoutShippingMethodForm, CountryForm, ReplaceCheckoutLineForm
from ..models import Checkout
from ..utils import (
    check_product_availability_and_warn,
    get_checkout_context,
    get_or_empty_db_checkout,
    get_shipping_price_estimate,
    is_valid_shipping_method,
    update_checkout_quantity,
)
from .discount import add_voucher_form, validate_voucher
from .shipping import anonymous_user_shipping_address_view, user_shipping_address_view
from .summary import (
    anonymous_summary_without_shipping,
    summary_with_shipping_view,
    summary_without_shipping,
)
from .validators import (
    validate_checkout,
    validate_is_shipping_required,
    validate_shipping_address,
    validate_shipping_method,
)


@get_or_empty_db_checkout(Checkout.objects.for_display())
@validate_checkout
def checkout_login(request, checkout):
    """Allow the user to log in prior to checkout."""
    if request.user.is_authenticated:
        return redirect("checkout:start")
    ctx = {"form": LoginForm()}
    return TemplateResponse(request, "checkout/login.html", ctx)


@get_or_empty_db_checkout(Checkout.objects.for_display())
@validate_checkout
@validate_is_shipping_required
def checkout_start(request, checkout):
    """Redirect to the initial step of checkout."""
    return redirect("checkout:shipping-address")


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
    is_valid_shipping_method(checkout, discounts)

    form = CheckoutShippingMethodForm(
        request.POST or None,
        discounts=discounts,
        instance=checkout,
        initial={"shipping_method": checkout.shipping_method},
    )
    if form.is_valid():
        form.save()
        return redirect("checkout:summary")

    ctx = get_checkout_context(checkout, discounts)
    ctx.update({"shipping_method_form": form})
    return TemplateResponse(request, "checkout/shipping_method.html", ctx)


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
    checkout_lines = []
    check_product_availability_and_warn(request, checkout)

    # refresh required to get updated checkout lines and it's quantity
    try:
        checkout = Checkout.objects.prefetch_related(
            "lines__variant__product__category"
        ).get(pk=checkout.pk)
    except Checkout.DoesNotExist:
        pass

    lines = checkout.lines.select_related("variant__product__product_type")
    lines = lines.prefetch_related(
        "variant__translations",
        "variant__product__translations",
        "variant__product__images",
        "variant__product__product_type__variant_attributes__translations",
        "variant__images",
        "variant__product__product_type__variant_attributes",
    )
    manager = request.extensions
    for line in lines:
        initial = {"quantity": line.quantity}
        form = ReplaceCheckoutLineForm(
            None,
            checkout=checkout,
            variant=line.variant,
            initial=initial,
            discounts=discounts,
        )
        total_line = manager.calculate_checkout_line_total(line, discounts)
        variant_price = quantize_price(total_line / line.quantity, total_line.currency)
        checkout_lines.append(
            {
                "variant": line.variant,
                "get_price": variant_price,
                "get_total": total_line,
                "form": form,
            }
        )

    default_country = get_user_shipping_country(request)
    country_form = CountryForm(initial={"country": default_country})
    shipping_price_range = get_shipping_price_estimate(
        checkout, discounts, country_code=default_country
    )

    context = get_checkout_context(
        checkout,
        discounts,
        currency=request.currency,
        shipping_range=shipping_price_range,
    )
    context.update(
        {
            "checkout_lines": checkout_lines,
            "country_form": country_form,
            "shipping_price_range": shipping_price_range,
        }
    )
    return TemplateResponse(request, "checkout/index.html", context)


@get_or_empty_db_checkout(checkout_queryset=Checkout.objects.for_display())
def checkout_shipping_options(request, checkout):
    """Display shipping options to get a price estimate."""
    country_form = CountryForm(request.POST or None)
    if country_form.is_valid():
        shipping_price_range = country_form.get_shipping_price_estimate(
            checkout, request.discounts
        )
    else:
        shipping_price_range = None
    ctx = {"shipping_price_range": shipping_price_range, "country_form": country_form}
    checkout_data = get_checkout_context(
        checkout,
        request.discounts,
        currency=request.currency,
        shipping_range=shipping_price_range,
    )
    ctx.update(checkout_data)
    return TemplateResponse(request, "checkout/_subtotal_table.html", ctx)


@get_or_empty_db_checkout(Checkout.objects.prefetch_related("lines__variant__product"))
def update_checkout_line(request, checkout, variant_id):
    """Update the line quantities."""
    if not request.is_ajax():
        return redirect("checkout:index")

    checkout_line = get_object_or_404(checkout.lines, variant_id=variant_id)
    discounts = request.discounts
    status = None
    form = ReplaceCheckoutLineForm(
        request.POST,
        checkout=checkout,
        variant=checkout_line.variant,
        discounts=discounts,
    )
    manager = request.extensions
    if form.is_valid():
        form.save()
        checkout.refresh_from_db()
        # Refresh obj from db and confirm that checkout still has this line
        checkout_line = checkout.lines.filter(variant_id=variant_id).first()
        line_total = zero_taxed_money(currency=settings.DEFAULT_CURRENCY)
        if checkout_line:
            line_total = manager.calculate_checkout_line_total(checkout_line, discounts)
        subtotal = get_display_price(line_total)
        response = {
            "variantId": variant_id,
            "subtotal": format_money(subtotal),
            "total": 0,
            "checkout": {"numItems": checkout.quantity, "numLines": len(checkout)},
        }

        checkout_total = manager.calculate_checkout_subtotal(checkout, discounts)
        checkout_total = get_display_price(checkout_total)
        response["total"] = format_money(checkout_total)
        local_checkout_total = to_local_currency(checkout_total, request.currency)
        if local_checkout_total is not None:
            response["localTotal"] = format_money(local_checkout_total)

        status = 200
    elif request.POST is not None:
        response = {"error": form.errors}
        status = 400
    return JsonResponse(response, status=status)


@get_or_empty_db_checkout()
def clear_checkout(request, checkout):
    """Clear checkout."""
    if not request.is_ajax():
        return redirect("checkout:index")
    checkout.lines.all().delete()
    update_checkout_quantity(checkout)
    response = {"numItems": 0}
    return JsonResponse(response)


@get_or_empty_db_checkout(checkout_queryset=Checkout.objects.for_display())
def checkout_dropdown(request, checkout):
    """Display a checkout summary suitable for displaying on all pages."""
    discounts = request.discounts
    manager = request.extensions

    def prepare_line_data(line):
        first_image = line.variant.get_first_image()
        if first_image:
            first_image = first_image.image
        return {
            "product": line.variant.product,
            "variant": line.variant,
            "quantity": line.quantity,
            "image": first_image,
            "line_total": manager.calculate_checkout_line_total(line, discounts),
            "variant_url": line.variant.get_absolute_url(),
        }

    if checkout.quantity == 0:
        data = {"quantity": 0}
    else:
        data = {
            "quantity": checkout.quantity,
            "total": manager.calculate_checkout_subtotal(checkout, discounts),
            "lines": [prepare_line_data(line) for line in checkout],
        }

    return render(request, "checkout_dropdown.html", data)
