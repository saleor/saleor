from django.template.response import TemplateResponse
from django.contrib import messages
from django.utils.translation import pgettext_lazy

from ..dashboard.views import staff_member_required
from ..product.utils import products_with_availability, products_for_homepage
from ..settings import IMPERSONATE_GET_PARAM


def home(request):
    products = products_for_homepage()[:8]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    # TODO: Get rid of url parameters
    if request.GET.get('action') == IMPERSONATE_GET_PARAM:
        msg = pgettext_lazy('Impersonation message',
                            'You are now logged as %s') % request.user.email
        messages.success(request, msg)
    return TemplateResponse(
        request, 'home.html',
        {'products': products, 'parent': None})


@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'styleguide.html')
