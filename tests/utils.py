from typing import Dict, Set, Union
from urllib.parse import urlparse

from prices import Money

from saleor.product.models import Product, ProductVariant


def get_url_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    return get_url_path(response["Location"])


def get_form_errors(response, form_name="form"):
    errors = response.context.get(form_name).errors
    return errors.get("__all__") if errors else []


def money(amount):
    return Money(amount, "USD")


def generate_attribute_map(obj: Union[Product, ProductVariant]) -> Dict[int, Set[int]]:
    """Generate a map from a product or variant instance.

    Useful to quickly compare the assigned attribute values against expected IDs.

    The below association map will be returned.

        {
            attribute_pk (int) => {attribute_value_pk (int), ...}
            ...
        }
    """

    qs = obj.attributes.select_related("assignment__attribute")
    qs = qs.prefetch_related("values")

    return {
        assignment.attribute.pk: {value.pk for value in assignment.values.all()}
        for assignment in qs
    }
