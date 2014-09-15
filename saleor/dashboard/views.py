from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ..order.models import Order, Payment


class StaffMemberOnlyMixin(object):
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(StaffMemberOnlyMixin, self).dispatch(*args, **kwargs)


class FilterByStatusMixin(object):
    def __init__(self, *args, **kwargs):
        super(FilterByStatusMixin, self).__init__(*args, **kwargs)
        status_choices = getattr(self, 'status_choices')
        self.statuses = {status[0]: status[1] for status in status_choices}
        self.status_order = getattr(self, 'status_order', [])

    def get_queryset(self):
        qs = super(FilterByStatusMixin, self).get_queryset()
        if self.statuses:
            active_filter = self.request.GET.get('status')
            if active_filter in self.statuses:
                qs = qs.filter(status=active_filter)
                self.active_filter = active_filter
            else:
                self.active_filter = None
        return qs

    def get_context_data(self):
        ctx = super(FilterByStatusMixin, self).get_context_data()
        ctx['active_filter'] = self.active_filter
        ctx['available_filters'] = self.get_filters()
        return ctx

    def get_filters(self):
        filters = [(name, self.statuses[name]) for name in self.status_order
                   if name in self.statuses]
        remain = [(name, verbose) for name, verbose in self.statuses.items()
                  if (name, verbose) not in filters]
        filters.extend(remain)
        return filters


class IndexView(StaffMemberOnlyMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super(IndexView, self).get_context_data(**kwargs)
        ctx['preauthorized_payments'] = self.get_preauthorized_payments()
        ctx['orders_to_ship'] = self.get_orders_to_ship()
        return ctx

    def get_preauthorized_payments(self):
        return Payment.objects.filter(status='preauth')

    def get_orders_to_ship(self):
        return Order.objects.filter(status='fully-paid')
