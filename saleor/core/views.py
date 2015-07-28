from django.template.response import TemplateResponse
from saleor.product.models import Product


def home(request):
    products = Product.objects.get_available_products()
    products = products.prefetch_related('categories', 'images',
                                         'variants__stock')
    return TemplateResponse(
        request, 'base.html',
        {'products': products, 'parent': None})
