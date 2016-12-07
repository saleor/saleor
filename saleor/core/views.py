from django.template.response import TemplateResponse

from ..product.utils import products_with_availability, products_with_details


def home(request):
    products = products_with_details(request.user)[:12]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    return TemplateResponse(
        request, 'base.html',
        {'products': products, 'parent': None})
