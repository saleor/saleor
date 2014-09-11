from django.db.models import Count, Max
from django.views.generic import ListView, DetailView
from ..views import StaffMemberOnlyMixin
from ...userprofile.models import User


class CustomerList(StaffMemberOnlyMixin, ListView):
    model = User
    template_name = 'dashboard/customer/list.html'
    paginate_by = 30

    def get_queryset(self):
        qs = super(CustomerList, self).get_queryset()
        open_order = ['new', 'payment-pending', 'fully-paid']
        qs = qs.prefetch_related('orders').filter(
            orders__status__in=open_order)
        qs = qs.annotate(num_orders=Count('orders', distinct=True),
                         last_order=Max('orders', distinct=True))
        return qs


class CustomerDetails(StaffMemberOnlyMixin, DetailView):
    model = User
    template_name = 'dashboard/customer/detail.html'
    context_object_name = 'customer'

    def get_queryset(self):
        qs = super(CustomerDetails, self).get_queryset()
        qs = qs.prefetch_related('orders', 'addresses').select_related(
            'default_billing_address')
        return qs
