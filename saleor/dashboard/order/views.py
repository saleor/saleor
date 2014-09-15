from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView, UpdateView
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from payments import PaymentError

from ...order.models import Order, Address
from ...userprofile.forms import AddressForm
from ..views import StaffMemberOnlyMixin, FilterByStatusMixin
from .forms import OrderNoteForm, ManagePaymentForm


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
        if 'payment_form' not in ctx:
            ctx['payment_form'] = self.payment_form_class(
                initial={'amount': self.object.get_total().gross})
        if 'note_form' not in ctx:
            ctx['note_form'] = self.note_form_class()

        last_payment_status = self.object.get_last_payment_status()
        ctx['can_capture'] = last_payment_status == 'preauth'
        ctx['can_release'] = last_payment_status == 'preauth'
        ctx['can_refund'] = last_payment_status == 'confirmed'

        ctx['notes'] = self.object.notes.all()
        ctx['payment'] = self.object.payments.last()
        return ctx

    def get_delivery_info(self):
        try:
            return self.object.groups.select_subclasses().get()
        except self.model.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        if 'release' in request.POST:
            self.handle_release_action()
        if 'payment_form' in request.POST:
            form = self.payment_form_class(request.POST)
            self.handle_payment_form(form, request.POST['payment_form'])
        else:
            form = self.note_form_class(request.POST)
            self.handle_note_form(form)
        return self.get(request, *args, **kwargs)

    def handle_release_action(self):
        payment = self.get_object().payments.last()
        error_msg = None
        if payment.status == 'preauth':
            try:
                payment.release(user=self.request.user)
            except PaymentError, e:
                error_msg = _('Payment gateway error: ') + e.message
                messages.error(self.request, error_msg)
            else:
                messages.success(self.request, _('Release successful'))

    def handle_payment_form(self, form, action):
        payment = self.get_object().payments.last()
        error_msg = None
        if form.is_valid():
            if action == 'capture' and payment.status == 'preauth':
                try:
                    payment.capture(
                        amount=form.cleaned_data['amount'],
                        user=self.request.user)
                except PaymentError, e:
                    error_msg = _('Payment gateway error: ') + e.message
                else:
                    messages.success(self.request, _('Funds captured'))

            elif action == 'refund' and payment.status == 'confirmed':
                try:
                    payment.refund(
                        amount=form.cleaned_data['amount'],
                        user=self.request.user)
                except PaymentError, e:
                    error_msg = _('Payment gateway error: ') + e.message
                else:
                    messages.success(self.request, _('Refund successful'))

        if error_msg:
            messages.error(self.request, error_msg)

    def handle_note_form(self, form):
        if form.is_valid():
            note = form.save(commit=False)
            note.order = self.get_object()
            note.user = self.request.user
            note.save()
            messages.success(self.request, _('Note saved'))
        else:
            messages.error(self.request, _('Form has errors'))


class AddressView(StaffMemberOnlyMixin, UpdateView):
    model = Address
    template_name = 'dashboard/order/address-edit.html'
    form_class = AddressForm

    def get_object(self, queryset=None):
        self.order = get_object_or_404(Order, pk=self.kwargs['order_pk'])
        address_type = self.kwargs['address_type']
        if address_type == 'billing':
            return self.order.billing_address
        elif address_type == 'shipping':
            delivery = self.order.groups.select_subclasses().get()
            return delivery.address

    def get_context_data(self, **kwargs):
        ctx = super(AddressView, self).get_context_data(**kwargs)
        ctx['order'] = self.order
        ctx['address_type'] = self.kwargs['address_type']
        return ctx

    def get_success_url(self):
        _type_str = self.kwargs['address_type'].capitalize()
        messages.success(
            self.request,
            _('%(address_type)s address updated' % {'address_type': _type_str})
        )
        return reverse('dashboard:order-details', kwargs={'pk': self.order.pk})
