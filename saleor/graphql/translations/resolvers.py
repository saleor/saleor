from ...product import models as product_models
from ...shipping import models as shipping_models


def resolve_translation(instance, _info, language_code):
    """Get translation object from instance based on language code."""
    return instance.translations.filter(language_code=language_code).first()


def resolve_shipping_methods(info):
    return shipping_models.ShippingMethod.objects.all()


def resolve_attribute_values(info):
    return product_models.AttributeValue.objects.all()
