import json

from django.template.response import TemplateResponse
from django.contrib import messages
from django.utils.translation import pgettext_lazy
from impersonate.views import impersonate as orig_impersonate, stop_impersonate

from .utils.schema import get_webpage_schema
from ..dashboard.views import staff_member_required
from ..product.utils import products_with_availability, products_for_homepage
from ..userprofile.models import User


def home(request):
    products = products_for_homepage()[:8]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    webpage_schema = get_webpage_schema(request)
    return TemplateResponse(
        request, 'home.html', {
            'parent': None,
            'products': products,
            'webpage_schema': json.dumps(webpage_schema)})


@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'styleguide.html')


def impersonate(request, uid):
    response = orig_impersonate(request, uid)
    if request.session.modified:
        msg = pgettext_lazy(
            'Impersonation message',
            'You are now logged as {}'.format(User.objects.get(pk=uid)))
        messages.success(request, msg)
    return response
