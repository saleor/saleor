from ...attribute import models as attribute_models
from ...core.tracing import traced_resolver
from ...discount import models as discount_models
from ...product import models as product_models
from ...shipping import models as shipping_models


@traced_resolver
def resolve_translation(instance, _info, language_code):
    """Get translation object from instance based on language code."""
    return instance.translations.filter(language_code=language_code).first()


@traced_resolver
def resolve_shipping_methods(info):
    return shipping_models.ShippingMethod.objects.all()


@traced_resolver
def resolve_attribute_values(info):
    return attribute_models.AttributeValue.objects.all()


@traced_resolver
def resolve_products(_info):
    return product_models.Product.objects.all()


@traced_resolver
def resolve_product_variants(_info):
    return product_models.ProductVariant.objects.all()


@traced_resolver
def resolve_sales(_info):
    return discount_models.Sale.objects.all()


@traced_resolver
def resolve_vouchers(_info):
    return discount_models.Voucher.objects.all()


@traced_resolver
def resolve_collections(_info):
    return product_models.Collection.objects.all()
