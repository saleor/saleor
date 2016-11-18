from django.template.response import TemplateResponse

from ..product.utils import products_with_availability, products_with_details


def home(request):
    products = products_with_details(request.user)[:12]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    return TemplateResponse(
        request, 'base.html',
        {'products': products, 'parent': None})


def demo(request):
    products = Product.objects.get_available_products()[:12]
    products = products.prefetch_related('categories', 'images',
                                         'variants__stock')
    return TemplateResponse(
        request, 'demo/home.html',
        {'products': products, 'parent': None})