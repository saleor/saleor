from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView, UpdateView
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from ...order.models import Order, Address
from ...userprofile.forms import AddressForm
from ..views import StaffMemberOnlyMixin, FilterByStatusMixin
from .forms import OrderNoteForm


class OrderListView(StaffMemberOnlyMixin, FilterByStatusMixin, ListView):
    template_name = 'dashboard/order/list.html'
    paginate_by = 20
    model = Order
    status_choices = Order.STATUS_CHOICES


class OrderDetails(StaffMemberOnlyMixin, DetailView):
    model = Order
    template_name = 'dashboard/order/detail.html'
    context_object_name = 'order'
    form_class = OrderNoteForm
    form_instance = None

    def get_queryset(self):
        qs = super(OrderDetails, self).get_queryset()
        qs = qs.prefetch_related('notes')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super(OrderDetails, self).get_context_data(**kwargs)
        if not self.form_instance:
            self.form_instance = self.form_class()
        ctx['notes_form'] = self.form_instance
        ctx['notes'] = self.object.notes.all()
        return ctx

    def get_delivery_info(self):
        try:
            return self.object.groups.select_subclasses().get()
        except self.model.DoesNotExist:
            return None

    def post(self, *args, **kwargs):
        form = self.form_class(self.request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.order = self.get_object()
            note.user = self.request.user
            note.save()
            messages.success(self.request, _('Note saved'))
        else:
            messages.error(self.request, _('Form has errors'))
        self.form_instance = form
        return self.get(*args, **kwargs)


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
