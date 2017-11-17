from django.template.response import TemplateResponse
from django.contrib import messages
from django.conf import settings
from django.utils.translation import pgettext_lazy
from impersonate.views import impersonate as orig_impersonate

from ..dashboard.views import staff_member_required
from ..product.utils import products_with_availability, products_for_homepage
from ..userprofile.models import User


def home(request):
    products = products_for_homepage()[:8]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    return TemplateResponse(
        request, 'home.html',
        {'products': products, 'parent': None})


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
