from .models import Product


def products_visible_to_user(user):
    if (user.is_authenticated() and
            user.is_active and user.is_staff):
        return Product.objects.all()
    else:
        return Product.objects.get_available_products()


def products_with_details(user):
    products = products_visible_to_user(user)
    products = products.select_subclasses()
    products = products.prefetch_related('categories', 'images',
                                         'variants__stock',
                                         'variants__variant_images__image',
                                         'attributes__values')
    return products
