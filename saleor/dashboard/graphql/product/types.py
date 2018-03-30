from ....graphql.utils import get_node
from ....product import models as product_models


def resolve_attributes():
    return product_models.ProductAttribute.objects.all().distinct()


def resolve_products(info, category_id):
    if category_id is not None:
        category = get_node(info, category_id, only_type=Category)
        return product_models.Product.objects.filter(
            category=category).distinct()
    return product_models.Product.objects.all().distinct()
