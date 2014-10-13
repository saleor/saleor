from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView, UpdateView
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.context_processors import csrf
from payments import PaymentError

from ...order.models import Order, OrderedItem, Address, DeliveryGroup
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

        ctx['notes'] = self.object.notes.all()
        if 'note_form' not in ctx:
            ctx['note_form'] = self.note_form_class()

        payment = self.get_object().payments.last()
        ctx['payment'] = payment
        if payment:
            ctx['can_capture'] = payment.status == 'preauth' \
                and self.object.status != 'cancelled'
            ctx['can_release'] = payment.status == 'preauth'
            ctx['can_refund'] = payment.status == 'confirmed'
            if payment.status == 'confirmed':
                amount = payment.captured_amount
            elif payment.status == 'preauth':
                amount = self.object.get_total().gross
            else:
                amount = None
            ctx['payment_form'] = self.payment_form_class(
                initial={'amount': amount})
            ctx['amount'] = amount
            if payment.status == 'refunded':
                ctx['refunded_amount'] = payment.total - payment.captured_amount
        else:
            ctx['can_capture'] = ctx['can_release'] = ctx['can_refund'] = False
            ctx['payment_form'] = self.payment_form_class()

        groups = self.object.groups.select_subclasses().all()
        for group in groups:
            group.can_ship = payment.status == 'confirmed' and group.status == 'new'
        ctx['delivery_groups'] = groups
        return ctx

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


class AddressView(StaffMemberOnlyMixin, UpdateView):
    model = Address
    template_name = 'dashboard/order/address-edit.html'
    form_class = AddressForm

    def dispatch(self, *args, **kwargs):
        if 'group_pk' in self.kwargs:
            self.address_type = 'shipping'
        else:
            self.address_type = 'billing'
        return super(AddressView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        self.order = get_object_or_404(Order, pk=self.kwargs['order_pk'])
        if self.address_type == 'billing':
            return self.order.billing_address
        else:
            delivery = self.order.groups.select_subclasses().get(
                pk=self.kwargs['group_pk'])
            return delivery.address

    def get_context_data(self, **kwargs):
        ctx = super(AddressView, self).get_context_data(**kwargs)
        ctx['order'] = self.order
        ctx['address_type'] = self.address_type
        return ctx

    def get_success_url(self):
        _type_str = self.address_type.capitalize()
        messages.success(
            self.request,
            _('%(address_type)s address updated' % {'address_type': _type_str})
        )
        return reverse('dashboard:order-details', kwargs={'pk': self.order.pk})


class OrderLineEdit(StaffMemberOnlyMixin, UpdateView):
    model = OrderedItem
    quantity_form = ChangeQuantityForm
    move_items_form = MoveItemsForm

    def get_context_data(self, **kwargs):
        ctx = super(OrderLineEdit, self).get_context_data(**kwargs)
        ctx['quantity_form'] = self.quantity_form(item=self.get_object())
        ctx['move_items_form'] = self.move_items_form(item=self.get_object())
        return ctx

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        ctx = self.get_context_data(*args, **kwargs)
        ctx.update(csrf(request))
        if request.is_ajax():
            template = 'dashboard/includes/modal_order_line_edit.html'
            rendered = render_to_string(template, ctx)
            return HttpResponse(rendered)
        else:
            return self.render_to_response(ctx)


class ShipDeliveryGroupModal(StaffMemberOnlyMixin, UpdateView):
    model = DeliveryGroup
    context_object_name = 'group'

    def get_queryset(self):
        return DeliveryGroup.objects.select_subclasses()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        ctx = self.get_context_data(*args, **kwargs)
        ctx.update(csrf(request))
        if request.is_ajax():
            template = 'dashboard/includes/modal_ship_delivery_group.html'
            rendered = render_to_string(template, ctx)
            return HttpResponse(rendered)
        else:
            return self.render_to_response(ctx)
