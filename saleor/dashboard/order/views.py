from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.sites.models import Site
from django.db import transaction
from django.db.models import F, Q
from django.forms import modelformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.context_processors import csrf
from django.template.response import TemplateResponse
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django.views.decorators.http import require_POST
from django_prices.templatetags import prices_i18n
from payments import PaymentStatus

from ...core.exceptions import InsufficientStock
from ...core.utils import get_paginator_items
from ...core.utils.taxes import (
    ZERO_MONEY, ZERO_TAXED_MONEY, get_taxes_for_address)
from ...order import CustomPaymentChoices, OrderStatus
from ...order.emails import (
    send_fulfillment_confirmation, send_fulfillment_update,
    send_order_confirmation)
from ...order.models import Fulfillment, FulfillmentLine, Order, OrderNote
from ...order.utils import update_order_prices, update_order_status
from ...shipping.models import ShippingMethodCountry
from ..views import staff_member_required
from .filters import OrderFilter
from .forms import (
    AddressForm, AddVariantToOrderForm, BaseFulfillmentLineFormSet,
    CancelFulfillmentForm, CancelOrderForm, CancelOrderLineForm,
    CapturePaymentForm, ChangeQuantityForm, CreateOrderFromDraftForm,
    FulfillmentForm, FulfillmentLineForm, FulfillmentTrackingNumberForm,
    OrderCustomerForm, OrderEditDiscountForm, OrderEditVoucherForm,
    OrderMarkAsPaidForm, OrderNoteForm, OrderRemoveCustomerForm,
    OrderRemoveShippingForm, OrderRemoveVoucherForm, OrderShippingForm,
    RefundPaymentForm, ReleasePaymentForm)
from .utils import (
    create_invoice_pdf, create_packing_slip_pdf, get_statics_absolute_url,
    save_address_in_order)


@staff_member_required
@permission_required('order.view_order')
def order_list(request):
    orders = Order.objects.prefetch_related('payments', 'lines', 'user')
    order_filter = OrderFilter(request.GET, queryset=orders)
    orders = get_paginator_items(
        order_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'orders': orders, 'filter_set': order_filter,
        'is_empty': not order_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/order/list.html', ctx)


@require_POST
@staff_member_required
@permission_required('order.edit_order')
def order_create(request):
    display_gross_prices = request.site.settings.display_gross_prices
    order = Order.objects.create(
        status=OrderStatus.DRAFT, display_gross_prices=display_gross_prices)
    msg = pgettext_lazy(
        'Dashboard message related to an order',
        'Draft order created')
    messages.success(request, msg)
    return redirect('dashboard:order-details', order_pk=order.pk)


@staff_member_required
@permission_required('order.edit_order')
def create_order_from_draft(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    status = 200
    form = CreateOrderFromDraftForm(request.POST or None, instance=order)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message related to an order',
            'Order created from draft order')
        order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        if form.cleaned_data.get('notify_customer'):
            send_order_confirmation.delay(order.pk)
            send_mail_msg = pgettext_lazy(
                'Dashboard message related to an order',
                'Order confirmation email was sent to user'
                '(%(email)s)') % {'email': order.get_user_current_email()}
            order.history.create(content=send_mail_msg, user=request.user)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    template = 'dashboard/order/modal/create_order.html'
    ctx = {'form': form, 'order': order}
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def remove_draft_order(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    if request.method == 'POST':
        order.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Draft order successfully removed')
        messages.success(request, msg)
        return redirect('dashboard:orders')
    template = 'dashboard/order/modal/remove_order.html'
    ctx = {'order': order}
    return TemplateResponse(request, template, ctx)


@staff_member_required
@permission_required('order.view_order')
def order_details(request, order_pk):
    qs = Order.objects.select_related(
        'user', 'shipping_address', 'billing_address').prefetch_related(
        'notes__user', 'payments', 'history__user', 'lines__variant__product',
        'fulfillments__lines__order_line')
    order = get_object_or_404(qs, pk=order_pk)
    all_payments = order.payments.exclude(status=PaymentStatus.INPUT)
    payment = order.get_last_payment()
    preauthorized = ZERO_TAXED_MONEY
    captured = ZERO_MONEY
    balance = captured - order.total.gross
    if payment:
        can_capture = (
            payment.status == PaymentStatus.PREAUTH and
            order.status not in {OrderStatus.DRAFT, OrderStatus.CANCELED})
        can_release = payment.status == PaymentStatus.PREAUTH
        can_refund = (
            payment.status == PaymentStatus.CONFIRMED and
            payment.variant != CustomPaymentChoices.MANUAL)
        preauthorized = payment.get_total_price()
        if payment.status == PaymentStatus.CONFIRMED:
            captured = payment.get_captured_price()
            balance = captured - order.total.gross
    else:
        can_capture = can_release = can_refund = False
    can_mark_as_paid = not order.payments.exists()
    ctx = {
        'order': order, 'all_payments': all_payments, 'payment': payment,
        'notes': order.notes.all(), 'events': order.history.all(),
        'captured': captured, 'balance': balance,
        'preauthorized': preauthorized,
        'can_capture': can_capture, 'can_release': can_release,
        'can_refund': can_refund, 'can_mark_as_paid': can_mark_as_paid,
        'order_fulfillments': order.fulfillments.all()}
    return TemplateResponse(request, 'dashboard/order/detail.html', ctx)


@staff_member_required
@permission_required('order.edit_order')
def order_add_note(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    note = OrderNote(order=order, user=request.user)
    form = OrderNoteForm(request.POST or None, instance=note)
    status = 200
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message related to an order',
            'Added note')
        messages.success(request, msg)
        if not order.is_draft():
            order.history.create(content=msg, user=request.user)
            if note.is_public:
                form.send_confirmation_email()
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    ctx.update(csrf(request))
    template = 'dashboard/order/modal/add_note.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def capture_payment(request, order_pk, payment_pk):
    orders = Order.objects.confirmed().prefetch_related('payments')
    order = get_object_or_404(orders, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    amount = order.total.quantize('0.01').gross
    form = CapturePaymentForm(request.POST or None, payment=payment,
                              initial={'amount': amount})
    if form.is_valid() and form.capture():
        amount = form.cleaned_data['amount']
        msg = pgettext_lazy(
            'Dashboard message related to a payment',
            'Captured %(amount)s') % {'amount': prices_i18n.amount(amount)}
        order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal/capture.html', ctx,
                            status=status)


@staff_member_required
@permission_required('order.edit_order')
def refund_payment(request, order_pk, payment_pk):
    orders = Order.objects.confirmed().prefetch_related('payments')
    order = get_object_or_404(orders, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    amount = payment.captured_amount
    form = RefundPaymentForm(request.POST or None, payment=payment,
                             initial={'amount': amount})
    if form.is_valid() and form.refund():
        amount = form.cleaned_data['amount']
        msg = pgettext_lazy(
            'Dashboard message related to a payment',
            'Refunded %(amount)s') % {'amount': prices_i18n.amount(amount)}
        order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal/refund.html', ctx,
                            status=status)


@staff_member_required
@permission_required('order.edit_order')
def release_payment(request, order_pk, payment_pk):
    orders = Order.objects.confirmed().prefetch_related('payments')
    order = get_object_or_404(orders, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    form = ReleasePaymentForm(request.POST or None, payment=payment)
    if form.is_valid() and form.release():
        msg = pgettext_lazy('Dashboard message', 'Released payment')
        order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal/release.html', ctx,
                            status=status)


@staff_member_required
@permission_required('order.edit_order')
def orderline_change_quantity(request, order_pk, line_pk):
    orders = Order.objects.drafts().prefetch_related('lines')
    order = get_object_or_404(orders, pk=order_pk)
    line = get_object_or_404(order.lines, pk=line_pk)
    form = ChangeQuantityForm(request.POST or None, instance=line)
    status = 200
    old_quantity = line.quantity
    if form.is_valid():
        msg = pgettext_lazy(
            'Dashboard message related to an order line',
            'Changed quantity for variant %(variant)s from'
            ' %(old_quantity)s to %(new_quantity)s') % {
                'variant': line.variant, 'old_quantity': old_quantity,
                'new_quantity': line.quantity}
        with transaction.atomic():
            form.save()
            messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'object': line, 'form': form}
    template = 'dashboard/order/modal/change_quantity.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def orderline_cancel(request, order_pk, line_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    line = get_object_or_404(order.lines, pk=line_pk)
    form = CancelOrderLineForm(data=request.POST or None, line=line)
    status = 200
    if form.is_valid():
        msg = pgettext_lazy(
            'Dashboard message related to an order line',
            'Canceled item %s') % line
        with transaction.atomic():
            form.cancel_line()
            messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'item': line, 'form': form}
    return TemplateResponse(
        request, 'dashboard/order/modal/cancel_line.html',
        ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def add_variant_to_order(request, order_pk):
    """Add variant in given quantity to an order."""
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    taxes = get_taxes_for_address(order.shipping_address)
    form = AddVariantToOrderForm(
        request.POST or None, order=order, discounts=request.discounts,
        taxes=taxes)
    status = 200
    if form.is_valid():
        msg_dict = {
            'quantity': form.cleaned_data.get('quantity'),
            'variant': form.cleaned_data.get('variant')}
        try:
            with transaction.atomic():
                form.save()
            msg = pgettext_lazy(
                'Dashboard message related to an order',
                'Added %(quantity)d x %(variant)s') % msg_dict
            messages.success(request, msg)
        except InsufficientStock:
            msg = pgettext_lazy(
                'Dashboard message related to an order',
                'Insufficient stock: could not add %(quantity)d x %(variant)s'
            ) % msg_dict
            messages.warning(request, msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    template = 'dashboard/order/modal/add_variant_to_order.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def order_address(request, order_pk, address_type):
    order = get_object_or_404(Order, pk=order_pk)
    update_prices = False
    if address_type == 'shipping':
        address = order.shipping_address
        success_msg = pgettext_lazy(
            'Dashboard message',
            'Updated shipping address')
        update_prices = True
    else:
        address = order.billing_address
        success_msg = pgettext_lazy(
            'Dashboard message',
            'Updated billing address')
    form = AddressForm(request.POST or None, instance=address)
    if form.is_valid():
        updated_address = form.save()
        if not address:
            save_address_in_order(order, updated_address, address_type)
        if update_prices:
            update_order_prices(order, request.discounts)
        if not order.is_draft():
            order.history.create(content=success_msg, user=request.user)
        messages.success(request, success_msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    ctx = {'order': order, 'address_type': address_type, 'form': form}
    return TemplateResponse(request, 'dashboard/order/address_form.html', ctx)


@staff_member_required
@permission_required('order.edit_order')
def order_customer_edit(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    form = OrderCustomerForm(request.POST or None, instance=order)
    status = 200
    if form.is_valid():
        form.save()
        update_order_prices(order, request.discounts)
        user_email = form.cleaned_data.get('user_email')
        user = form.cleaned_data.get('user')
        if user_email:
            msg = pgettext_lazy(
                'Dashboard message',
                '%s email assigned to an order') % user_email
        elif user:
            msg = pgettext_lazy(
                'Dashboard message',
                '%s user assigned to an order') % user
        else:
            msg = pgettext_lazy(
                'Dashboard message',
                'Guest user assigned to an order')
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    return TemplateResponse(
        request, 'dashboard/order/modal/edit_customer.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def order_customer_remove(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    form = OrderRemoveCustomerForm(request.POST or None, instance=order)
    if form.is_valid():
        form.save()
        update_order_prices(order, request.discounts)
        msg = pgettext_lazy(
            'Dashboard message',
            'Customer removed from an order')
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    return redirect('dashboard:order-customer-edit', order_pk=order.pk)


@staff_member_required
@permission_required('order.edit_order')
def order_shipping_edit(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    taxes = get_taxes_for_address(order.shipping_address)
    form = OrderShippingForm(request.POST or None, instance=order, taxes=taxes)
    status = 200
    if form.is_valid():
        form.save()
        msg = pgettext_lazy('Dashboard message', 'Shipping updated')
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    return TemplateResponse(
        request, 'dashboard/order/modal/edit_shipping.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def order_shipping_remove(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    form = OrderRemoveShippingForm(request.POST or None, instance=order)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy('Dashboard message', 'Shipping removed')
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    return redirect('dashboard:order-shipping-edit', order_pk=order.pk)


@staff_member_required
@permission_required('order.edit_order')
def order_discount_edit(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    form = OrderEditDiscountForm(request.POST or None, instance=order)
    status = 200
    if form.is_valid():
        form.save()
        msg = pgettext_lazy('Dashboard message', 'Discount updated')
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    return TemplateResponse(
        request, 'dashboard/order/modal/edit_discount.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def order_voucher_edit(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    form = OrderEditVoucherForm(request.POST or None, instance=order)
    status = 200
    if form.is_valid():
        form.save()
        msg = pgettext_lazy('Dashboard message', 'Voucher updated')
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    return TemplateResponse(
        request, 'dashboard/order/modal/edit_voucher.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def cancel_order(request, order_pk):
    order = get_object_or_404(Order.objects.confirmed(), pk=order_pk)
    status = 200
    form = CancelOrderForm(request.POST or None, order=order)
    if form.is_valid():
        msg = pgettext_lazy('Dashboard message', 'Order canceled')
        with transaction.atomic():
            form.cancel_order()
            if form.cleaned_data.get('restock'):
                restock_msg = npgettext_lazy(
                    'Dashboard message',
                    'Restocked %(quantity)d item',
                    'Restocked %(quantity)d items',
                    'quantity') % {'quantity': order.get_total_quantity()}
                order.history.create(content=restock_msg, user=request.user)
            order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
        # TODO: send status confirmation email
    elif form.errors:
        status = 400
    ctx = {'form': form, 'order': order}
    return TemplateResponse(
        request, 'dashboard/order/modal/cancel_order.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def order_voucher_remove(request, order_pk):
    order = get_object_or_404(Order.objects.drafts(), pk=order_pk)
    form = OrderRemoveVoucherForm(request.POST or None, instance=order)
    if form.is_valid():
        msg = pgettext_lazy('Dashboard message', 'Removed voucher from order')
        with transaction.atomic():
            form.remove_voucher()
            messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    return redirect('dashboard:order-voucher-edit', order_pk=order.pk)


@staff_member_required
@permission_required('order.view_order')
def order_invoice(request, order_pk):
    orders = Order.objects.confirmed().prefetch_related(
        'user', 'shipping_address', 'billing_address', 'voucher')
    order = get_object_or_404(orders, pk=order_pk)
    absolute_url = get_statics_absolute_url(request)
    pdf_file, order = create_invoice_pdf(order, absolute_url)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    name = "invoice-%s.pdf" % order.id
    response['Content-Disposition'] = 'filename=%s' % name
    return response


@staff_member_required
@permission_required('order.edit_order')
def mark_order_as_paid(request, order_pk):
    order = get_object_or_404(Order.objects.confirmed(), pk=order_pk)
    status = 200
    form = OrderMarkAsPaidForm(request.POST or None, order=order)
    if form.is_valid():
        msg = pgettext_lazy(
            'Dashboard message',
            'Order manually marked as paid')
        with transaction.atomic():
            form.save()
            order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'form': form, 'order': order}
    return TemplateResponse(
        request, 'dashboard/order/modal/mark_as_paid.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def fulfillment_packing_slips(request, order_pk, fulfillment_pk):
    orders = Order.objects.confirmed().prefetch_related(
        'user', 'shipping_address', 'billing_address')
    order = get_object_or_404(orders, pk=order_pk)
    fulfillments = order.fulfillments.prefetch_related(
        'lines', 'lines__order_line')
    fulfillment = get_object_or_404(fulfillments, pk=fulfillment_pk)
    absolute_url = get_statics_absolute_url(request)
    pdf_file, order = create_packing_slip_pdf(order, fulfillment, absolute_url)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    name = "packing-slip-%s.pdf" % (order.id,)
    response['Content-Disposition'] = 'filename=%s' % name
    return response


@staff_member_required
@permission_required('order.edit_order')
def fulfill_order_lines(request, order_pk):
    orders = Order.objects.confirmed().prefetch_related('lines')
    order = get_object_or_404(orders, pk=order_pk)
    unfulfilled_lines = order.lines.filter(
        quantity_fulfilled__lt=F('quantity'))
    status = 200
    form = FulfillmentForm(
        request.POST or None, order=order, instance=Fulfillment())
    FulfillmentLineFormSet = modelformset_factory(
        FulfillmentLine, form=FulfillmentLineForm,
        extra=len(unfulfilled_lines), formset=BaseFulfillmentLineFormSet)
    initial = [
        {'order_line': line, 'quantity': line.quantity_unfulfilled}
        for line in unfulfilled_lines]
    formset = FulfillmentLineFormSet(
        request.POST or None, queryset=FulfillmentLine.objects.none(),
        initial=initial)
    all_forms_valid = all([line_form.is_valid() for line_form in formset])
    if all_forms_valid and form.is_valid():
        forms_to_save = [
            line_form for line_form in formset
            if line_form.cleaned_data.get('quantity') > 0]
        if forms_to_save:
            fulfillment = form.save()
            quantity_fulfilled = 0
            for line_form in forms_to_save:
                line = line_form.save(commit=False)
                line.fulfillment = fulfillment
                line.save()
                quantity_fulfilled += line_form.cleaned_data.get('quantity')
            # update to refresh prefetched lines quantity_fulfilled
            order = orders.get(pk=order_pk)
            update_order_status(order)
            msg = npgettext_lazy(
                'Dashboard message related to an order',
                'Fulfilled %(quantity_fulfilled)d item',
                'Fulfilled %(quantity_fulfilled)d items',
                'quantity_fulfilled') % {
                    'quantity_fulfilled': quantity_fulfilled}
            order.history.create(content=msg, user=request.user)
            if form.cleaned_data.get('send_mail'):
                send_fulfillment_confirmation.delay(order.pk, fulfillment.pk)
                send_mail_msg = pgettext_lazy(
                    'Dashboard message related to an order',
                    'Shipping confirmation email was sent to user'
                    '(%(email)s)') % {'email': order.get_user_current_email()}
                order.history.create(content=send_mail_msg, user=request.user)
        else:
            msg = pgettext_lazy(
                'Dashboard message related to an order', 'No items fulfilled')
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {
        'form': form, 'formset': formset, 'order': order,
        'unfulfilled_lines': unfulfilled_lines}
    template = 'dashboard/order/fulfillment.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def cancel_fulfillment(request, order_pk, fulfillment_pk):
    orders = Order.objects.confirmed().prefetch_related('fulfillments')
    order = get_object_or_404(orders, pk=order_pk)
    fulfillment = get_object_or_404(order.fulfillments, pk=fulfillment_pk)
    status = 200
    form = CancelFulfillmentForm(request.POST or None, fulfillment=fulfillment)
    if form.is_valid():
        msg = pgettext_lazy(
            'Dashboard message', 'Fulfillment #%(fulfillment)s canceled') % {
                'fulfillment': fulfillment.composed_id}
        with transaction.atomic():
            form.cancel_fulfillment()
            if form.cleaned_data.get('restock'):
                restock_msg = npgettext_lazy(
                    'Dashboard message',
                    'Restocked %(quantity)d item',
                    'Restocked %(quantity)d items',
                    'quantity') % {
                        'quantity': fulfillment.get_total_quantity()}
                order.history.create(content=restock_msg, user=request.user)
            order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'form': form, 'order': order, 'fulfillment': fulfillment}
    return TemplateResponse(
        request, 'dashboard/order/modal/cancel_fulfillment.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def change_fulfillment_tracking(request, order_pk, fulfillment_pk):
    orders = Order.objects.confirmed().prefetch_related('fulfillments')
    order = get_object_or_404(orders, pk=order_pk)
    fulfillment = get_object_or_404(order.fulfillments, pk=fulfillment_pk)
    status = 200
    form = FulfillmentTrackingNumberForm(
        request.POST or None, instance=fulfillment)
    if form.is_valid():
        form.save()
        if fulfillment.tracking_number:
            msg = pgettext_lazy(
                'Dashboard message',
                'Fulfillment #%(fulfillment)s tracking number changed to: '
                '#%(tracking_number)s') % {
                    'fulfillment': fulfillment.composed_id,
                    'tracking_number': fulfillment.tracking_number}
        else:
            msg = pgettext_lazy(
                'Dashboard message',
                'Fulfillment #%(fulfillment)s tracking number removed') % {
                    'fulfillment': fulfillment.composed_id}
        order.history.create(content=msg, user=request.user)
        if form.cleaned_data.get('send_mail'):
            send_fulfillment_update.delay(order.pk, fulfillment.pk)
            send_mail_msg = pgettext_lazy(
                'Dashboard message related to an order',
                'Shipping update email was sent to user (%(email)s)') % {
                    'email': order.get_user_current_email()}
            order.history.create(content=send_mail_msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'form': form, 'order': order, 'fulfillment': fulfillment}
    return TemplateResponse(
        request, 'dashboard/order/modal/fulfillment_tracking.html', ctx,
        status=status)


@staff_member_required
def ajax_order_shipping_methods_list(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    queryset = ShippingMethodCountry.objects.select_related(
        'shipping_method').order_by('shipping_method__name', 'price')

    if order.shipping_address:
        country_code = order.shipping_address.country.code
        queryset = queryset.unique_for_country_code(country_code)

    search_query = request.GET.get('q', '')
    if search_query:
        queryset = queryset.filter(
            Q(shipping_method__name__icontains=search_query) |
            Q(price__icontains=search_query))

    shipping_methods = [
        {'id': method.pk, 'text': method.get_ajax_label()}
        for method in queryset]
    return JsonResponse({'results': shipping_methods})
