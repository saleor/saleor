from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError

from ...warehouse.models import Stock

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...account import models as account_models
    from ...product.models import ProductVariant
    from ..account import types as account_types


def get_used_attribute_values_for_variant(variant):
    """Create a dict of attributes values for variant.

    Sample result is:
    {
        "attribute_1_global_id": ["ValueAttr1_1"],
        "attribute_2_global_id": ["ValueAttr2_1"]
    }
    """
    attribute_values = defaultdict(list)
    for assigned_variant_attribute in variant.attributes.all():
        attribute = assigned_variant_attribute.attribute
        attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
        for attr_value in assigned_variant_attribute.values.all():
            attribute_values[attribute_id].append(attr_value.slug)
    return attribute_values


def get_used_variants_attribute_values(product):
    """Create list of attributes values for all existing `ProductVariants` for product.

    Sample result is:
    [
        {
            "attribute_1_global_id": ["ValueAttr1_1"],
            "attribute_2_global_id": ["ValueAttr2_1"]
        },
        ...
        {
            "attribute_1_global_id": ["ValueAttr1_2"],
            "attribute_2_global_id": ["ValueAttr2_2"]
        }
    ]
    """
    variants = (
        product.variants.prefetch_related("attributes__values")
        .prefetch_related("attributes__assignment")
        .all()
    )
    used_attribute_values = []
    for variant in variants:
        attribute_values = get_used_attribute_values_for_variant(variant)
        used_attribute_values.append(attribute_values)
    return used_attribute_values


@transaction.atomic
def create_stocks(
    variant: "ProductVariant", stocks_data: List[Dict[str, str]], warehouses: "QuerySet"
):
    try:
        Stock.objects.bulk_create(
            [
                Stock(
                    product_variant=variant,
                    warehouse=warehouse,
                    quantity=stock_data["quantity"],
                )
                for stock_data, warehouse in zip(stocks_data, warehouses)
            ]
        )
    except IntegrityError:
        msg = "Stock for one of warehouses already exists for this product variant."
        raise ValidationError(msg)


def get_country_for_stock_and_tax_calculation(
    destination_address: Optional[
        Union["account_types.AddressInput", "account_models.Address"]
    ] = None,
    company_address: Optional["account_models.Address"] = None,
) -> str:
    """Get country code needed for stock quantity validation and tax calculations.

    Country code for checkout is based on shipping address. If shipping address is not
    provided, try to use the company address configured in the shop settings. If this
    address is not set, fallback to the `DEFAULT_COUNTRY` setting.
    """
    if destination_address and destination_address.country:
        return destination_address.country
    elif company_address and company_address.country:
        return company_address.country.code
    else:
        return settings.DEFAULT_COUNTRY
