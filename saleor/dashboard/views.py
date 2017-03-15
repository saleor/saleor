from django.conf import settings
from django.contrib.admin.views.decorators import \
    staff_member_required as _staff_member_required
from django.db.models import Q, Sum
from django.template.response import TemplateResponse
from payments import PaymentStatus

from ..order.models import Order, Payment
from ..order import OrderStatus
from ..product.models import Product


def staff_member_required(f):
    return _staff_member_required(f, login_url='account_login')


@staff_member_required
def index(request):
    orders_to_ship = Order.objects.filter(status=OrderStatus.FULLY_PAID)
    orders_to_ship = (orders_to_ship
                      .select_related('user')
                      .prefetch_related('groups', 'groups__items', 'payments'))
    payments = Payment.objects.filter(
        status=PaymentStatus.PREAUTH).order_by('-created')
    payments = payments.select_related('order', 'order__user')
    low_stock = get_low_stock_products()
    ctx = {'preauthorized_payments': payments,
           'orders_to_ship': orders_to_ship,
           'low_stock': low_stock}
    return TemplateResponse(request, 'dashboard/index.html', ctx)


@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'dashboard/styleguide/index.html', {})


def get_low_stock_products():
    threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 10)
    products = Product.objects.annotate(
        total_stock=Sum('variants__stock__quantity'))
    return products.filter(Q(total_stock__lte=threshold)).distinct()
