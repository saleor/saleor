from typing import Dict, Iterable

from django.db.models import Exists, OuterRef, Q

from .models import AssignedProductAttribute, AssignedVariantAttribute

T_PRODUCT_FILTER_QUERIES = Dict[int, Iterable[int]]


def filter_products_by_attributes_values(qs, queries: T_PRODUCT_FILTER_QUERIES):
    filters = [
        Q(
            Exists(
                AssignedProductAttribute.objects.filter(
                    product__id=OuterRef("pk"), values__pk__in=values
                )
            )
        )
        | Q(
            Exists(
                AssignedVariantAttribute.objects.filter(
                    variant__product__id=OuterRef("pk"), values__pk__in=values,
                )
            )
        )
        for values in queries.values()
    ]

    return qs.filter(*filters)
