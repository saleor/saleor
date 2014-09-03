from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView
from ...order.models import Order
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
        billing_address = self.object.billing_address
        delivery_info = self.get_delivery_info()
        if delivery_info:
            delivery_address = delivery_info.address
        else:
            delivery_address = None
        ctx['addresses_equal'] = delivery_address == billing_address
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
