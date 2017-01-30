from django.template.response import TemplateResponse

from ..product.utils import products_with_availability, products_with_details


def home(request):
    products = products_with_details(request.user).filter(is_featured=True)[:8]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    return TemplateResponse(
        request, 'home.html',
        {'products': products, 'parent': None})
