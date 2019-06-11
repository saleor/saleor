from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext

from ...account.models import Address
from ...core import analytics
from ...core.exceptions import InsufficientStock
from ...discount.models import NotApplicable
from ..forms import CheckoutNoteForm
from ..utils import (
    create_order,
    get_checkout_context,
    get_taxes_for_checkout,
    prepare_order_data,
    update_billing_address_in_anonymous_checkout,
    update_billing_address_in_checkout,
    update_billing_address_in_checkout_with_shipping,
)


def _handle_order_placement(request, checkout):
    """Try to create an order and redirect the user as necessary.

    This function creates an order from checkout and performs post-create actions
    such as removing the checkout instance, sending order notification email
    and creating order history events.
    """
    try:
        # Run checks an prepare the data for order creation
        order_data = prepare_order_data(
            checkout=checkout,
            tracking_code=analytics.get_client_id(request),
            discounts=request.discounts,
            taxes=get_taxes_for_checkout(checkout, request.taxes),
        )
    except InsufficientStock:
        return redirect("checkout:index")
    except NotApplicable:
        messages.warning(
            request, pgettext("Checkout warning", "Please review your checkout.")
        )
        return redirect("checkout:summary")

    # Push the order data into the database
    order = create_order(checkout=checkout, order_data=order_data, user=request.user)

    # remove checkout after order is created
    checkout.delete()

    # Redirect the user to the payment page
    return redirect("order:payment", token=order.token)


def summary_with_shipping_view(request, checkout):
    """Display order summary with billing forms for a logged in user.

    Will create an order if all data is valid.
    """
    note_form = CheckoutNoteForm(request.POST or None, instance=checkout)
    if note_form.is_valid():
        note_form.save()

    user_addresses = (
        checkout.user.addresses.all() if checkout.user else Address.objects.none()
    )

    addresses_form, address_form, updated = update_billing_address_in_checkout_with_shipping(  # noqa
        checkout, user_addresses, request.POST or None, request.country
    )

    if updated:
        return _handle_order_placement(request, checkout)

    taxes = get_taxes_for_checkout(checkout, request.taxes)
    ctx = get_checkout_context(checkout, request.discounts, taxes)
    ctx.update(
        {
            "additional_addresses": user_addresses,
            "address_form": address_form,
            "addresses_form": addresses_form,
            "note_form": note_form,
        }
    )
    return TemplateResponse(request, "checkout/summary.html", ctx)


def anonymous_summary_without_shipping(request, checkout):
    """Display order summary with billing forms for an unauthorized user.

    Will create an order if all data is valid.
    """
    note_form = CheckoutNoteForm(request.POST or None, instance=checkout)
    if note_form.is_valid():
        note_form.save()

    user_form, address_form, updated = update_billing_address_in_anonymous_checkout(
        checkout, request.POST or None, request.country
    )

    if updated:
        return _handle_order_placement(request, checkout)

    taxes = get_taxes_for_checkout(checkout, request.taxes)
    ctx = get_checkout_context(checkout, request.discounts, taxes)
    ctx.update(
        {"address_form": address_form, "note_form": note_form, "user_form": user_form}
    )
    return TemplateResponse(request, "checkout/summary_without_shipping.html", ctx)


def summary_without_shipping(request, checkout):
    """Display order summary for cases where shipping is not required.

    Will create an order if all data is valid.
    """
    note_form = CheckoutNoteForm(request.POST or None, instance=checkout)
    if note_form.is_valid():
        note_form.save()

    user_addresses = checkout.user.addresses.all()

    addresses_form, address_form, updated = update_billing_address_in_checkout(
        checkout, user_addresses, request.POST or None, request.country
    )

    if updated:
        return _handle_order_placement(request, checkout)

    taxes = get_taxes_for_checkout(checkout, request.taxes)
    ctx = get_checkout_context(checkout, request.discounts, taxes)
    ctx.update(
        {
            "additional_addresses": user_addresses,
            "address_form": address_form,
            "addresses_form": addresses_form,
            "note_form": note_form,
        }
    )
    return TemplateResponse(request, "checkout/summary_without_shipping.html", ctx)
