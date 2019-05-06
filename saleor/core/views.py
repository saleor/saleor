import json

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from impersonate.views import impersonate as orig_impersonate

from ..account.models import User
from ..dashboard.views import staff_member_required
from ..product.utils import products_for_homepage
from ..product.utils.availability import products_with_availability
from ..seo.schema.webpage import get_webpage_schema


def home(request):
    products = products_for_homepage(
        request.user,
        request.site.settings.homepage_collection)[:8]
    products = list(products_with_availability(
        products, discounts=request.discounts, taxes=request.taxes,
        local_currency=request.currency))
    webpage_schema = get_webpage_schema(request)
    return TemplateResponse(
        request, 'home.html', {
            'parent': None,
            'products': products,
            'webpage_schema': json.dumps(webpage_schema)})


@staff_member_required
def styleguide(request):
    from saleor.events import OrderEventsEmails
    from saleor.order.models import Order
    from saleor.events.order import OrderEventManager

    for i in range(2):
        order = Order.objects.first()
        e1 = OrderEventManager().email_sent_event(
            order=order, email_type=OrderEventsEmails.TRACKING_UPDATED, user=request.user)
        e2 = e1.email_sent_event(order=order, email_type=OrderEventsEmails.TRACKING_UPDATED, user=request.user)
        assert len(e1.instances) == 2
        e1.save()
    return TemplateResponse(request, 'styleguide.html')


def impersonate(request, uid):
    response = orig_impersonate(request, uid)
    if request.session.modified:
        msg = pgettext_lazy(
            'Impersonation message',
            'You are now logged as {}'.format(User.objects.get(pk=uid)))
        messages.success(request, msg)
    return response


def handle_404(request, exception=None):
    return TemplateResponse(request, '404.html', status=404)


def manifest(request):
    return TemplateResponse(
        request, 'manifest.json', content_type='application/json')
