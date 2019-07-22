import graphene_django_optimizer as gql_optimizer

from ...product import models as product_models
from ...shipping import models as shipping_models


def resolve_translation(instance, _info, language_code):
    """Gets translation object from instance based on language code."""
    return instance.translations.filter(language_code=language_code).first()


def resolve_shipping_methods(info):
    qs = shipping_models.ShippingMethod.objects.all()
    return gql_optimizer.query(qs, info)


def resolve_attribute_values(info):
    qs = product_models.AttributeValue.objects.all()
    return gql_optimizer.query(qs, info)
