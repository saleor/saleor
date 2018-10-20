from django.conf import settings
from django.contrib.admin.views.decorators import (
    staff_member_required as _staff_member_required, user_passes_test)
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.db.models import Q, Sum
from django.template.response import TemplateResponse

from ..order.models import Order
from ..payment import ChargeStatus
from ..payment.models import Payment
from ..product.models import Product


def staff_member_required(f):
    return _staff_member_required(f, login_url='account:login')


def superuser_required(
        view_func=None, redirect_field_name=REDIRECT_FIELD_NAME,
        login_url='account:login'):
    """Check if the user is logged in and is a superuser.

    Otherwise redirects to the login page.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


@staff_member_required
def index(request):
    paginate_by = 10
    orders_to_ship = Order.objects.ready_to_fulfill().select_related(
        'user').prefetch_related('lines', 'payments')
    payments = Payment.objects.filter(
        is_active=True, charge_status=ChargeStatus.NOT_CHARGED
    ).order_by('-created')
    payments = payments.select_related('order', 'order__user')
    low_stock = get_low_stock_products()
    ctx = {'preauthorized_payments': payments[:paginate_by],
           'orders_to_ship': orders_to_ship[:paginate_by],
           'low_stock': low_stock[:paginate_by]}
    return TemplateResponse(request, 'dashboard/index.html', ctx)


@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'dashboard/styleguide/index.html', {})


def get_low_stock_products():
    threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 10)
    products = Product.objects.annotate(
        total_stock=Sum('variants__quantity'))
    return products.filter(Q(total_stock__lte=threshold)).distinct()
