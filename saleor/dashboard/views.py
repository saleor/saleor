from django.conf import settings
from django.contrib.admin.views.decorators import \
    staff_member_required as _staff_member_required
from django.db.models import Q, Sum
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic.edit import FormMixin

from ..order.models import Order, Payment
from ..product.models import Product
from .order.forms import OrderFilterForm


def staff_member_required(f):
    return _staff_member_required(f, login_url='account_login')


class StaffMemberOnlyMixin(object):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(StaffMemberOnlyMixin, self).dispatch(*args, **kwargs)


class FilterByStatusMixin(FormMixin):
    form_class = OrderFilterForm

    def __init__(self):
        super(FilterByStatusMixin, self).__init__()
        self.active_filter = None

    def get_queryset(self):
        queryset = super(FilterByStatusMixin, self).get_queryset()
        active_filter = self.request.GET.get('status')
        if active_filter:
            self.active_filter = active_filter
            queryset = queryset.filter(status=self.active_filter)
        return queryset

    def get_initial(self):
        initial = super(FilterByStatusMixin, self).get_initial()
        if self.active_filter:
            initial['status'] = self.active_filter
        return initial

    def get_context_data(self):
        ctx = super(FilterByStatusMixin, self).get_context_data()
        ctx['form'] = self.get_form()
        return ctx


@staff_member_required
def index(request):
    orders_to_ship = Order.objects.filter(status='fully-paid')
    orders_to_ship = (orders_to_ship
                      .select_related('user')
                      .prefetch_related('groups', 'groups__items', 'payments'))
    payments = Payment.objects.filter(status='preauth').order_by('-created')
    payments = payments.select_related('order', 'order__user')
    low_stock = get_low_stock_products()
    ctx = {'preauthorized_payments': payments,
           'orders_to_ship': orders_to_ship,
           'low_stock': low_stock}
    return TemplateResponse(request, 'dashboard/index.html', ctx)


def get_low_stock_products():
    threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 10)
    products = Product.objects.annotate(
        total_stock=Sum('variants__stock__quantity'))
    return products.filter(Q(total_stock__lte=threshold)).distinct()
