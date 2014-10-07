from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView, UpdateView
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.context_processors import csrf
from payments import PaymentError

from ...order.models import Order, Address
from ...userprofile.forms import AddressForm
from ..views import StaffMemberOnlyMixin, FilterByStatusMixin
from .forms import OrderNoteForm, ManagePaymentForm, OrderContentFormset


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
    order_formset_class = OrderContentFormset

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

        ctx['order_formset'] = self.order_formset_class(
            order=self.object)

        return ctx

    def get_delivery_info(self):
        try:
            return self.object.groups.select_subclasses().get()
        except self.model.DoesNotExist:
            return None

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
            form = self.payment_form_class(request.POST)
            self.handle_payment_form(form, request.POST['payment_form'])
        elif 'note_form' in request.POST:
            form = self.note_form_class(request.POST)
            self.handle_note_form(form)
        elif 'order_formset' in request.POST:
            formset = self.order_formset_class(
                request.POST or None,
                order=self.get_object())
            self.handle_order_formset(formset)
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

    def handle_payment_form(self, form, action):
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

    def handle_note_form(self, form):
        if form.is_valid():
            note = form.save(commit=False)
            note.order = self.get_object()
            note.user = self.request.user
            note.save()
            messages.success(self.request, _('Note saved'))
        else:
            messages.error(self.request, _('Form has errors'))

    def handle_order_formset(self, formset):
        if formset.is_valid():
            if formset.has_changed():
                formset.save(user=self.request.user)
                messages.success(self.request, _('Quantities updated'))
        else:
            messages.error(self.request, _('Problem with updating quantities'))


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
