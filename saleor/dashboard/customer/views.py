from django.db.models import Count, Max, Q
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from .forms import CustomerSearchForm
from ..views import StaffMemberOnlyMixin
from ...userprofile.models import User


class CustomerList(StaffMemberOnlyMixin, ListView, FormMixin):
    model = User
    template_name = 'dashboard/customer/list.html'
    paginate_by = 30
    form_class = CustomerSearchForm
    context_object_name = 'customers'

    def dispatch(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)
        return super(CustomerList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(CustomerList, self).get_queryset()
        qs = self._annotate(qs)
        return self.apply_search(qs)

    def get_context_data(self, **kwargs):
        ctx = super(CustomerList, self).get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['render_search'] = self.form.is_valid()
        ctx['have_open_orders'] = self.get_users_with_open_orders()
        return ctx

    def get_users_with_open_orders(self):
        qs = super(CustomerList, self).get_queryset()
        qs = self._annotate(qs)
        open_order = ['new', 'payment-pending', 'fully-paid']
        return qs.filter(orders__status__in=open_order)

    def apply_search(self, queryset):
        if self.form.is_valid():
            return self.apply_search_filters(queryset, self.form.cleaned_data)
        else:
            return queryset

    def apply_search_filters(self, queryset, data):
        data = self._normalize_form_data(data)
        if data['email']:
            queryset = queryset.filter(email__icontains=data['email'])
        if data['name']:
            parts = data['name'].split()
            if len(parts) == 2:
                query = (Q(addresses__first_name__icontains=parts[0])
                         | Q(addresses__last_name__icontains=parts[1])) \
                    | (Q(addresses__first_name__icontains=parts[1])
                        | Q(addresses__last_name__icontains=parts[0]))
            else:
                query = Q(addresses__first_name__icontains=data['name']) \
                    | Q(addresses__last_name__istartswith=data['name'])
            queryset = queryset.filter(query).distinct()
        return queryset

    def post(self, request, **kwargs):
        return self.get(request, **kwargs)

    def _annotate(self, queryset):
        return queryset.prefetch_related('orders', 'addresses').annotate(
            num_orders=Count('orders', distinct=True),
            last_order=Max('orders', distinct=True))

    def _normalize_form_data(self, data):
        for k in data.keys():
            data[k] = data[k].strip()
        return data


class CustomerDetails(StaffMemberOnlyMixin, DetailView):
    model = User
    template_name = 'dashboard/customer/detail.html'
    context_object_name = 'customer'

    def get_queryset(self):
        qs = super(CustomerDetails, self).get_queryset()
        qs = qs.prefetch_related('orders', 'addresses').select_related(
            'default_billing_address')
        return qs
