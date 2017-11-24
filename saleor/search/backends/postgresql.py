from ...product.models import Product
from django.contrib.postgres.search import SearchVector


def search(phrase):
    obj = Product.objects.annotate(search=SearchVector('name', 'description'))
    return obj.filter(search=phrase)
