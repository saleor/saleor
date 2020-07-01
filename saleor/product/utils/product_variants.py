from ...graphql.core.utils import from_global_id_strict_type
from ...product.models import Product


def get_products_without_variants(products_list):
    """Return list of product's ids without variants."""
    products_ids = get_products_from_global_ids(products_list)
    products_without_variants = Product.objects.filter(
        id__in=products_ids, variants__isnull=True
    ).values_list("id", flat=True)
    return list(products_without_variants)


def get_products_from_global_ids(product_global_ids):
    """Return list of products ids generated from global id."""
    product_ids = []
    for product_global_id in product_global_ids:
        product_id = from_global_id_strict_type(product_global_id, only_type="Product")
        product_ids.append(product_id)

    return product_ids
