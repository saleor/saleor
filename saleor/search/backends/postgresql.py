from ...product.models import Product


def search(phrase):
    return Product.objects.none()
