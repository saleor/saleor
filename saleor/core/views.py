from django.template.response import TemplateResponse

from ..product.models import Product


def home(request):
    products = Product.objects.get_available_products()[:6]
    products = products.prefetch_related('categories', 'images',
                                         'variants__stock')
    return TemplateResponse(
        request, 'home.html',
        {'products': products, 'parent': None})
