from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.core.context_processors import csrf
from payments import PaymentError
from prices import Price

from ...order.models import Order, OrderedItem, DeliveryGroup
from ...userprofile.forms import AddressForm
from ..views import StaffMemberOnlyMixin, FilterByStatusMixin
from .forms import (OrderNoteForm, ManagePaymentForm, MoveItemsForm,
                    ChangeQuantityForm)


class OrderListView(StaffMemberOnlyMixin, FilterByStatusMixin, ListView):
    template_name = 'dashboard/order/list.html'
    paginate_by = 20
    model = Order
    status_choices = Order.STATUS_CHOICES
    status_order = ['new', 'payment-pending', 'fully-paid', 'shipped',
                    'cancelled']


class OrderDetails(StaffMemberOnlyMixin, DetailView):
    model = Order
    template_name = 'dashboard/order/detail.html'
    context_object_name = 'order'
    payment_form_class = ManagePaymentForm
    note_form_class = OrderNoteForm

    def get_queryset(self):
        qs = super(OrderDetails, self).get_queryset()
        qs = qs.prefetch_related('notes')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(OrderDetails, self).get_context_data(**kwargs)
        payment = self.get_object().payments.last()
        captured = refunded = preauthorized = None
        payment_form_initial = {'amount': self.object.get_total().gross}

        if payment:
            ctx['can_capture'] = payment.status == 'preauth' \
                and self.object.status != 'cancelled'
            ctx['can_release'] = payment.status == 'preauth'
            ctx['can_refund'] = payment.status == 'confirmed'

            preauthorized = Price(payment.total, currency=payment.currency)

            if payment.status == 'confirmed':
                captured = Price(payment.captured_amount,
                                 currency=payment.currency)
                payment_form_initial = {'amount': captured.gross}

            if payment.status == 'refunded':
                refunded = Price(payment.total - payment.captured_amount,
                                 currency=payment.currency)
        else:
            ctx['can_capture'] = ctx['can_release'] = ctx['can_refund'] = False

        ctx['note_form'] = self.note_form_class()
        ctx['payment_form'] = self.payment_form_class(payment_form_initial)

        ctx['delivery_groups'] = self.get_delivery_groups(payment)
        ctx['notes'] = self.object.notes.all()
        ctx['payment'] = payment
        ctx['captured'] = captured
        ctx['preauthorized'] = preauthorized
        ctx['refunded'] = refunded
        return ctx

    def get_delivery_groups(self, payment):
        groups = self.object.groups.select_subclasses().all()
        for group in groups:
            group.can_ship = payment and payment.status == 'confirmed' and \
                group.status == 'new'
        return groups

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        ctx = self.get_context_data()
        payment = ctx['payment']
        if request.is_ajax() and 'action' in request.GET:
            action = request.GET['action']
            ctx.update({'action': action, 'currency': payment.currency,
                        'captured': payment.captured_amount})
            if action == 'release':
                template = 'dashboard/includes/modal_release.html'
            else:
                template = 'dashboard/includes/modal_capture_refund.html'
            ctx.update(csrf(request))
            rendered = render_to_string(template, ctx)
            return HttpResponse(rendered)
        else:
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if 'release_action' in request.POST:
            self.handle_release_action()
        elif 'payment_form' in request.POST:
            self.handle_payment_form()
        elif 'note_form' in request.POST:
            self.handle_note_form()
        elif 'line_action' in request.POST:
            self.handle_line_action()
        elif 'shipping_action' in request.POST:
            self.handle_shipping_action()
        return self.get(request, *args, **kwargs)

    def handle_release_action(self):
        payment = self.get_object().payments.last()
        error_msg = None
        if payment.status == 'preauth':
            try:
                payment.release(user=self.request.user)
            except PaymentError as e:
                error_msg = _('Payment gateway error: ') + e.message
                messages.error(self.request, error_msg)
            else:
                messages.success(self.request, _('Release successful'))

    def handle_payment_form(self):
        action = self.request.POST['payment_form']
        form = self.payment_form_class(self.request.POST)
        payment = self.get_object().payments.last()
        error_msg = None
        if form.is_valid():
            if action == 'capture' and payment.status == 'preauth':
                try:
                    payment.capture(
                        amount=form.cleaned_data['amount'],
                        user=self.request.user)
                except PaymentError as e:
                    error_msg = _('Payment gateway error: ') + e.message
                else:
                    messages.success(self.request, _('Funds captured'))

            elif action == 'refund' and payment.status == 'confirmed':
                try:
                    payment.refund(
                        amount=form.cleaned_data['amount'],
                        user=self.request.user)
                except PaymentError as e:
                    error_msg = _('Payment gateway error: ') + e.message
                except ValueError as e:
                    error_msg = e.message
                else:
                    messages.success(self.request, _('Refund successful'))
        if error_msg:
            messages.error(self.request, error_msg)

    def handle_note_form(self):
        form = self.note_form_class(self.request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.order = self.get_object()
            note.user = self.request.user
            note.save()
            messages.success(self.request, _('Note saved'))
        else:
            messages.error(self.request, _('Form has errors'))

    def handle_line_action(self):
        action = self.request.POST['line_action']
        item = OrderedItem.objects.get(pk=self.request.POST['item_pk'])
        if action == 'move_items':
            form = MoveItemsForm(self.request.POST, item=item)
        elif action == 'change_quantity':
            form = ChangeQuantityForm(self.request.POST, item=item)
        if form.is_valid():
            form.save(user=self.request.user)
            messages.success(self.request, _('Order line updated'))
        else:
            messages.error(self.request, _('Cannot update order line'))

    def handle_shipping_action(self):
        group_pk = self.request.POST['shipping_action']
        order = self.get_object()
        group = order.groups.get(pk=group_pk)
        if group.status == 'new':
            group.change_status('shipped')
            msg = _('Shipped delivery group #%s' % group.pk)
            messages.success(self.request, msg)
            order.history.create(status=order.status,
                                 comment=msg,
                                 user=self.request.user)

            statuses = [g.status for g in order.groups.all()]
            if 'shipped' in statuses and 'new' not in statuses:
                order.change_status('shipped')


def address_view(request, order_pk, group_pk=None):
    address_type = 'shipping' if group_pk else 'billing'
    order = Order.objects.get(pk=order_pk)
    if address_type == 'shipping':
        address = order.groups.select_subclasses().get(pk=group_pk).address
    else:
        address = order.billing_address
    form = AddressForm(request.POST or None, instance=address)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if address_type == 'shipping':
                msg = _('Updated shipping address for group #%s' % group_pk)
            else:
                msg = _('Updated billing address')
            order.history.create(comment=msg, status=order.status,
                                 user=request.user)
            messages.success(request, msg)
            return redirect('dashboard:order-details', pk=order.pk)
    ctx = {'order': order, 'address_type': address_type, 'form': form}
    return TemplateResponse(request, 'dashboard/order/address-edit.html', ctx)


def order_line_edit(request, pk):
    item = OrderedItem.objects.get(pk=pk)
    quantity_form = ChangeQuantityForm(item=item)
    move_items_form = MoveItemsForm(item=item)
    ctx = {'object': item, 'quantity_form': quantity_form,
           'move_items_form': move_items_form}
    ctx.update(csrf(request))
    if request.is_ajax():
        template = 'dashboard/includes/modal_order_line_edit.html'
        rendered = render_to_string(template, ctx)
        return HttpResponse(rendered)


def ship_delivery_group_modal(request, pk):
    group = DeliveryGroup.objects.select_subclasses().get(pk=pk)
    ctx = {'group': group}
    ctx.update(csrf(request))
    if request.is_ajax():
        template = 'dashboard/includes/modal_ship_delivery_group.html'
        rendered = render_to_string(template, ctx)
        return HttpResponse(rendered)
