from __future__ import unicode_literals

from django.contrib import messages
from django.core.context_processors import csrf
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django_prices.templatetags.prices_i18n import gross
from prices import Price

from ...order.models import Order, OrderedItem, OrderNote
from ...userprofile.forms import AddressForm
from ..views import (StaffMemberOnlyMixin, FilterByStatusMixin,
                     staff_member_required)
from .forms import (OrderNoteForm, MoveItemsForm,
                    ChangeQuantityForm, ShipGroupForm, CapturePaymentForm,
                    ReleasePaymentForm, RefundPaymentForm)


class OrderListView(StaffMemberOnlyMixin, FilterByStatusMixin, ListView):
    template_name = 'dashboard/order/list.html'
    paginate_by = 20
    model = Order

    def get_queryset(self):
        qs = super(OrderListView, self).get_queryset()
        return qs.prefetch_related(
            'groups', 'payments', 'groups__items').select_related('user')


@staff_member_required
def order_details(request, order_pk):
    qs = (Order.objects
          .select_related('user', 'shipping_address', 'billing_address')
          .prefetch_related('notes', 'payments', 'history',
                            'groups', 'groups__items'))
    order = get_object_or_404(qs, pk=order_pk)
    notes = order.notes.all()
    all_payments = order.payments.all()
    payment = order.payments.last()
    groups = list(order)
    captured = preauthorized = Price(0, currency=order.total.currency)
    if payment:
        can_capture = (payment.status == 'preauth' and
                       order.status != 'cancelled')
        can_release = payment.status == 'preauth'
        can_refund = payment.status == 'confirmed'
        preauthorized = payment.get_total_price()
        if payment.status == 'confirmed':
            captured = payment.get_captured_price()
    else:
        can_capture = can_release = can_refund = False

    ctx = {'order': order, 'all_payments': all_payments, 'payment': payment,
           'notes': notes, 'groups': groups, 'captured': captured,
           'preauthorized': preauthorized, 'can_capture': can_capture,
           'can_release': can_release, 'can_refund': can_refund}
    return TemplateResponse(request, 'dashboard/order/detail.html', ctx)


@staff_member_required
def order_add_note(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    note = OrderNote(order=order, user=request.user)
    form = OrderNoteForm(request.POST or None, instance=note)
    status = 200
    if form.is_valid():
        form.save()
        msg = _('Added note')
        order.create_history_entry(comment=msg, user=request.user)
        messages.success(request, msg)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    ctx.update(csrf(request))
    template = 'dashboard/order/modal_add_note.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
def capture_payment(request, order_pk, payment_pk):
    order = get_object_or_404(Order, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    amount = order.total.quantize('0.01').gross
    form = CapturePaymentForm(request.POST or None, payment=payment,
                              initial={'amount': amount})
    if form.is_valid() and form.capture():
        amount = form.cleaned_data['amount']
        msg = _('Captured %(amount)s') % {'amount': gross(amount)}
        payment.order.create_history_entry(comment=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal_capture.html', ctx,
                            status=status)


@staff_member_required
def refund_payment(request, order_pk, payment_pk):
    order = get_object_or_404(Order, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    amount = payment.captured_amount
    form = RefundPaymentForm(request.POST or None, payment=payment,
                             initial={'amount': amount})
    if form.is_valid() and form.refund():
        amount = form.cleaned_data['amount']
        msg = _('Refunded %(amount)s') % {'amount': gross(amount)}
        payment.order.create_history_entry(comment=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal_refund.html', ctx,
                            status=status)


@staff_member_required
def release_payment(request, order_pk, payment_pk):
    order = get_object_or_404(Order, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    form = ReleasePaymentForm(request.POST or None, payment=payment)
    if form.is_valid() and form.release():
        msg = _('Released payment')
        payment.order.create_history_entry(comment=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal_release.html', ctx,
                            status=status)


@staff_member_required
def orderline_change_quantity(request, order_pk, line_pk):
    order = get_object_or_404(Order, pk=order_pk)
    item = get_object_or_404(OrderedItem.objects.filter(
        delivery_group__order=order), pk=line_pk)
    form = ChangeQuantityForm(request.POST or None, instance=item)
    status = 200
    old_quantity = item.quantity
    if form.is_valid():
        with transaction.atomic():
            form.save()
        msg = _(
            'Changed quantity for product %(product)s from'
            ' %(old_quantity)s to %(new_quantity)s') % {
                'product': item.product, 'old_quantity': old_quantity,
                'new_quantity': item.quantity}
        order.create_history_entry(comment=msg, user=request.user)
        messages.success(request, msg)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'object': item, 'form': form}
    template = 'dashboard/order/modal_change_quantity.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
def orderline_split(request, order_pk, line_pk):
    order = get_object_or_404(Order, pk=order_pk)
    item = get_object_or_404(OrderedItem.objects.filter(
        delivery_group__order=order), pk=line_pk)
    form = MoveItemsForm(request.POST or None, item=item)
    line_pk = None
    if item:
        line_pk = item.pk
    status = 200
    if form.is_valid():
        old_group = item.delivery_group
        how_many = form.cleaned_data['quantity']
        with transaction.atomic():
            target_group = form.move_items()
        if not old_group.pk:
            old_group = _('removed group')
        msg = _(
            'Moved %(how_many)s items %(item)s from %(old_group)s'
            ' to %(new_group)s') % {
                'how_many': how_many, 'item': item, 'old_group': old_group,
                'new_group': target_group}
        order.create_history_entry(comment=msg, user=request.user)
        messages.success(request, msg)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'object': item, 'form': form, 'line_pk': line_pk}
    template = 'dashboard/order/modal_split_order_line.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
def ship_delivery_group(request, order_pk, group_pk):
    order = get_object_or_404(Order, pk=order_pk)
    group = get_object_or_404(order.groups.all(), pk=group_pk)
    form = ShipGroupForm(request.POST or None, instance=group)
    status = 200
    if form.is_valid():
        with transaction.atomic():
            form.save()
        msg = _('Shipped %s') % group
        messages.success(request, msg)
        group.order.create_history_entry(comment=msg, user=request.user)
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'group': group, 'form': form}
    template = 'dashboard/order/modal_ship_delivery_group.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
def address_view(request, order_pk, address_type):
    order = Order.objects.get(pk=order_pk)
    if address_type == 'shipping':
        address = order.shipping_address
        success_msg = _('Updated shipping address')
    else:
        address = order.billing_address
        success_msg = _('Updated billing address')
    form = AddressForm(request.POST or None, instance=address)
    status = 200
    if form.is_valid():
        form.save()
        order.create_history_entry(comment=success_msg, user=request.user)
        messages.success(request, success_msg)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'address_type': address_type, 'form': form}
    return TemplateResponse(request, 'dashboard/order/modal_address_edit.html',
                            ctx, status=status)
