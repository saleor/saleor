from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required \
    as _staff_member_required
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from prices import Price

from ..order.models import Order, Payment


def staff_member_required(f):
    return _staff_member_required(f, login_url='registration:login')


class StaffMemberOnlyMixin(object):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(StaffMemberOnlyMixin, self).dispatch(*args, **kwargs)


class FilterByStatusMixin(object):
    def __init__(self, *args, **kwargs):
        super(FilterByStatusMixin, self).__init__(*args, **kwargs)
        status_choices = getattr(self, 'status_choices')
        self.statuses = dict(status_choices)
        self.status_order = getattr(self, 'status_order', [])

    def get_queryset(self):
        queryset = super(FilterByStatusMixin, self).get_queryset()
        if self.statuses:
            active_filter = self.request.GET.get('status')
            if active_filter in self.statuses:
                queryset = queryset.filter(status=active_filter)
                self.active_filter = active_filter
            else:
                self.active_filter = None
        return queryset

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


@staff_member_required
def index(request):
    orders_to_ship = Order.objects.filter(status='fully-paid')
    payments = Payment.objects.filter(status='preauth').order_by('-created')

    show_running_out = hasattr(settings, 'STOCKABLE_PRODUCTS')
    running_out = products_running_out() if show_running_out else []

    ctx = {'preauthorized_payments': payments, 'orders_to_ship': orders_to_ship,
           'show_running_out': show_running_out, 'running_out': running_out}
    return TemplateResponse(request, 'dashboard/index.html', ctx)


def products_running_out():
    product_classes = settings.STOCKABLE_PRODUCTS
    try:
        threshold = settings.STOCK_THRESHOLD
    except AttributeError:
        threshold = 10
    products = []
    for cls in product_classes:
        Product = import_string(cls)
        products.extend(Product.objects.filter(stock__lte=threshold))
    return products
