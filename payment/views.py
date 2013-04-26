from django.conf import settings
from django.http.response import Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from order import check_order_status
from payment.forms import PaymentMethodsForm, PaymentDeledeForm
from payments import RedirectNeeded, PaymentItem, get_payment_model

Payment = get_payment_model()


def get_payment_items_from_order(order):
    items = [PaymentItem(name=item.product_name, quantity=item.quantity,
                         price=item.unit_price_gross, sku=item.product.sku,
                         currency=settings.SATCHLESS_DEFAULT_CURRENCY)
             for item in order.get_items()]
    return items


def get_payment_from_order(variant, order):
    total = order.get_total()
    try:
        return order.payments.get(variant=variant, status='waiting')
    except Payment.DoesNotExist:
        billing = order.billing_address
        return Payment(
            order=order, variant=variant,
            total=total.gross, tax=total.tax, currency=total.currency,
            delivery=order.get_delivery_total().gross,
            billing_first_name=billing.first_name,
            billing_last_name=billing.last_name,
            billing_address_1=billing.street_address_1,
            billing_address_2=billing.street_address_2,
            billing_city=billing.city,
            billing_postcode=billing.postal_code,
            billing_country_code=billing.country,
            billing_country_area=billing.country_area)


@check_order_status
def index(request, order):
    form = PaymentMethodsForm(request.POST or None)
    try:
        waiting_payment = order.payments.get(status='waiting')
    except Payment.DoesNotExist:
        waiting_payment = None
        waiting_payment_form = None
    else:
        waiting_payment_form = PaymentDeledeForm(
            None, order=order, initial={'payment_id': waiting_payment.id})
    if form.is_valid() and not waiting_payment:
        payment_method = form.cleaned_data['method']
        return redirect('order:payment:details', token=order.token,
                        variant=payment_method)
    return TemplateResponse(request, 'payment/index.html',
                            {'form': form, 'order': order,
                             'waiting_payment': waiting_payment,
                             'waiting_payment_form': waiting_payment_form})


@check_order_status
def details(request, order, variant):
    order.change_status('payment-pending')
    items = get_payment_items_from_order(order)
    awaiting_payments = order.payments.filter(status='waiting').exists()
    payment = get_payment_from_order(variant, order)
    if awaiting_payments:
        return redirect('order:payment:index', token=order.token)
    try:
        form = payment.get_form(data=request.POST or None, ordered_items=items)
    except ValueError as e:
        raise Http404(e)
    except RedirectNeeded as redirect_to:
        return redirect(str(redirect_to))
    if form.is_valid():
        payment.save()
        return redirect(form.cleaned_data['next'])
    template = 'payment/%s.html' % variant
    return TemplateResponse(request, [template, 'payment/default.html'],
                            {'form': form, 'payment': payment})


@check_order_status
def delete(request, order):
    form = PaymentDeledeForm(request.POST or None, order=order)
    if form.is_valid():
        form.save()
        return redirect('order:payment:index', token=order.token)
    return HttpResponseForbidden()
