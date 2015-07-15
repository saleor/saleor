from __future__ import unicode_literals

from django.contrib import messages
from django.core.context_processors import csrf
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from payments import PaymentError
from prices import Price

from ...order.models import Order, OrderedItem, OrderNote
from ...userprofile.forms import AddressForm
from ..views import (StaffMemberOnlyMixin, FilterByStatusMixin,
                     staff_member_required)
from .forms import (OrderNoteForm, ManagePaymentForm, MoveItemsForm,
                    ChangeQuantityForm, ShipGroupForm)


class OrderListView(StaffMemberOnlyMixin, FilterByStatusMixin, ListView):
    template_name = 'dashboard/order/list.html'
    paginate_by = 20
    model = Order

    def get_queryset(self):
        qs = super(OrderListView, self).get_queryset()
        return qs.prefetch_related('groups')


@staff_member_required
def order_details(request, order_pk):
    order = get_object_or_404(Order.objects.prefetch_related(
        'notes', 'payments', 'history', 'groups'), pk=order_pk)
    notes = order.notes.all()
    payment = order.payments.last()
    groups = list(order)
    captured = preauthorized = Price(0, currency=order.get_total().currency)
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

    ctx = {'order': order, 'payment': payment, 'notes': notes, 'groups': groups,
           'captured': captured, 'preauthorized': preauthorized,
           'can_capture': can_capture, 'can_release': can_release,
           'can_refund': can_refund}
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
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'object': order, 'form': form}
    ctx.update(csrf(request))
    template = 'dashboard/order/modal_add_note.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
def manage_payment(request, order_pk, payment_pk, action):
    order = get_object_or_404(Order, pk=order_pk)
    payment = get_object_or_404(order.payments.all(), pk=payment_pk)
    form = ManagePaymentForm(request.POST or None, payment=payment)
    status = 200
    if form.is_valid():
        try:
            form.handle_action(action, request.user)
        except (PaymentError, ValueError) as e:
            messages.error(request, _('Payment gateway error: %s') % e.message)
        else:
            amount = form.cleaned_data['amount']
            currency = payment.currency
            if action == 'capture':
                comment = _('Captured %(amount)s %(currency)s') % {
                    'amount': amount, 'currency': currency}
                payment.order.create_history_entry(comment=comment,
                                                   user=request.user)
            elif action == 'refund':
                comment = _('Refunded %(amount)s %(currency)s') % {
                    'amount': amount, 'currency': currency}
                payment.order.create_history_entry(comment=comment,
                                                   user=request.user)
            elif action == 'release':
                comment = _('Released payment')
                payment.order.create_history_entry(comment=comment,
                                                   user=request.user)
    elif form.errors:
        status = 400
    amount = 0
    if action == 'release':
        template = 'dashboard/order/modal_release.html'
    else:
        if action == 'refund':
            amount = payment.captured_amount
        elif action == 'capture':
            amount = payment.order.get_total().gross
        template = 'dashboard/order/modal_capture_refund.html'
    initial = {'amount': amount, 'action': action}
    form = ManagePaymentForm(payment=payment, initial=initial)
    ctx = {'form': form, 'action': action, 'currency': payment.currency,
           'captured': payment.captured_amount, 'payment': payment}
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
def orderline_change_quantity(request, order_pk, line_pk):
    order = get_object_or_404(Order, pk=order_pk)
    item = get_object_or_404(OrderedItem.objects.filter(
        delivery_group__order=order), pk=line_pk)
    form = ChangeQuantityForm(request.POST or None, instance=item)
    status = 200
    if form.is_valid():
        old_quantity = item.quantity
        with transaction.atomic():
            form.save()
        msg = _(
            'Changed quantity for product %(product)s from'
            ' %(old_quantity)s to %(new_quantity)s') % {
                'product': item.product, 'old_quantity': old_quantity,
                'new_quantity': item.quantity}
        order.create_history_entry(comment=msg, user=request.user)
        return redirect('dashboard:order-details', order_pk=order_pk)
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
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'object': item, 'form': form}
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
    ctx = {'order': order, 'group': group}
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
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'address_type': address_type, 'form': form}
    return TemplateResponse(request, 'dashboard/order/modal_address_edit.html',
                            ctx, status=status)
