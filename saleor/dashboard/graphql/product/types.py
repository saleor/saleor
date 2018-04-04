from ....product import models as product_models


def resolve_attributes():
    return product_models.ProductAttribute.objects.all().distinct()
