from django.template.response import TemplateResponse

from ..product.utils import (categories_for_homepage,
                             products_with_availability, products_for_homepage)


def home(request):
    products = products_for_homepage()[:8]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    featured_categories = categories_for_homepage(3)
    return TemplateResponse(
        request, 'home.html',
        {'products': products, 'parent': None,
         'featured_categories': featured_categories})
