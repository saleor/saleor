from django.template.response import TemplateResponse

from ..product.utils import products_with_availability, products_for_homepage

HOME_HTML = 'home.html'

def home(request):
    products = products_for_homepage()[:8]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    return TemplateResponse(
        request, 'home.html',
        {'products': products, 'parent': None})
