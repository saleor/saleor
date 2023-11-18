from collections import defaultdict
from typing import TYPE_CHECKING, Union

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, Value, prefetch_related_objects
from django.db.models.expressions import Exists, OuterRef

from ..attribute import AttributeInputType
from ..attribute.models import (
    AssignedProductAttributeValue,
    Attribute,
    AttributeProduct,
)
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from ..core.utils.editorjs import clean_editor_js
from .models import Product

if TYPE_CHECKING:
    from django.db.models import QuerySet

PRODUCT_SEARCH_FIELDS = ["name", "description_plaintext"]
PRODUCT_FIELDS_TO_PREFETCH = [
    "variants__attributes__values",
    "variants__attributes",
    "attributevalues__value",
    "product_type__attributeproduct__attribute",
]

PRODUCTS_BATCH_SIZE = 300
# Setting threshold to 300 results in about 350MB of memory usage
# when testing locally. Should be adjusted after some time by running
# update task on a large dataset and measuring the total time, memory usage
# and time of a single SQL statement.


def _prep_product_search_vector_index(products):
    prefetch_related_objects(products, *PRODUCT_FIELDS_TO_PREFETCH)
    for product in products:
        product.search_vector = FlatConcatSearchVector(
            *prepare_product_search_vector_value(product, already_prefetched=True)
        )
        product.search_index_dirty = False

    Product.objects.bulk_update(
        products, ["search_vector", "updated_at", "search_index_dirty"]
    )


def update_products_search_vector(products: "QuerySet", use_batches=True):
    if use_batches:
        last_id = 0
        while True:
            products_batch = list(products.filter(id__gt=last_id)[:PRODUCTS_BATCH_SIZE])
            if not products_batch:
                break
            last_id = products_batch[-1].id
            _prep_product_search_vector_index(products_batch)
    else:
        _prep_product_search_vector_index(products)


def prepare_product_search_vector_value(
    product: "Product", *, already_prefetched=False
) -> list[NoValidationSearchVector]:
    if not already_prefetched:
        prefetch_related_objects([product], *PRODUCT_FIELDS_TO_PREFETCH)

    search_vectors = [
        NoValidationSearchVector(Value(product.name), config="simple", weight="A"),
        NoValidationSearchVector(
            Value(product.description_plaintext), config="simple", weight="C"
        ),
        *generate_attributes_search_vector_value(
            product,
        ),
        *generate_variants_search_vector_value(product),
    ]
    return search_vectors


def generate_variants_search_vector_value(
    product: "Product",
) -> list[NoValidationSearchVector]:
    variants = list(product.variants.all()[: settings.PRODUCT_MAX_INDEXED_VARIANTS])

    search_vectors = [
        NoValidationSearchVector(
            Value(variant.sku), Value(variant.name), config="simple", weight="A"
        )
        if variant.sku
        else NoValidationSearchVector(Value(variant.name), config="simple", weight="A")
        for variant in variants
        if variant.sku or variant.name
    ]
    if search_vectors:
        for variant in variants:
            search_vectors += generate_attributes_search_vector_value_with_assignment(
                variant.attributes.all()[: settings.PRODUCT_MAX_INDEXED_ATTRIBUTES]
            )
    return search_vectors


def generate_attributes_search_vector_value(
    product: "Product",
) -> list[NoValidationSearchVector]:
    """Prepare `search_vector` value for assigned attributes.

    Method should receive assigned attributes with prefetched `values`
    """
    product_attributes = AttributeProduct.objects.filter(
        product_type_id=product.product_type_id
    )
    attributes = Attribute.objects.filter(
        Exists(product_attributes.filter(attribute_id=OuterRef("id")))
    ).order_by("attributeproduct__sort_order")[
        : settings.PRODUCT_MAX_INDEXED_ATTRIBUTES
    ]

    assigned_values = AssignedProductAttributeValue.objects.filter(
        product_id=product.pk
    )
    prefetch_related_objects(assigned_values, "value")

    search_vectors = []

    values_map = defaultdict(list)
    for av in assigned_values:
        values_map[av.value.attribute_id].append(av.value)

    for attribute in attributes:
        values = values_map[attribute.pk][
            : settings.PRODUCT_MAX_INDEXED_ATTRIBUTE_VALUES
        ]

        search_vectors += get_search_vectors_for_values(attribute, values)
    return search_vectors


def generate_attributes_search_vector_value_with_assignment(
    assigned_attributes: "QuerySet",
) -> list[NoValidationSearchVector]:
    """Prepare `search_vector` value for assigned attributes.

    Method should receive assigned attributes with prefetched `values`
    and `assignment__attribute`.
    """
    search_vectors = []
    for assigned_attribute in assigned_attributes:
        attribute = assigned_attribute.assignment.attribute
        values = assigned_attribute.values.all()[
            : settings.PRODUCT_MAX_INDEXED_ATTRIBUTE_VALUES
        ]
        search_vectors += get_search_vectors_for_values(attribute, values)
    return search_vectors


def get_search_vectors_for_values(
    attribute: Attribute, values: Union[list, "QuerySet"]
) -> list[NoValidationSearchVector]:
    search_vectors = []

    input_type = attribute.input_type
    if input_type in [AttributeInputType.DROPDOWN, AttributeInputType.MULTISELECT]:
        search_vectors += [
            NoValidationSearchVector(Value(value.name), config="simple", weight="B")
            for value in values
        ]
    elif input_type == AttributeInputType.RICH_TEXT:
        search_vectors += [
            NoValidationSearchVector(
                Value(clean_editor_js(value.rich_text, to_string=True)),
                config="simple",
                weight="B",
            )
            for value in values
        ]
    elif input_type == AttributeInputType.PLAIN_TEXT:
        search_vectors += [
            NoValidationSearchVector(
                Value(value.plain_text), config="simple", weight="B"
            )
            for value in values
        ]
    elif input_type == AttributeInputType.NUMERIC:
        unit = attribute.unit
        search_vectors += [
            NoValidationSearchVector(
                Value(value.name + " " + unit if unit else value.name),
                config="simple",
                weight="B",
            )
            for value in values
        ]
    elif input_type in [AttributeInputType.DATE, AttributeInputType.DATE_TIME]:
        search_vectors += [
            NoValidationSearchVector(
                Value(value.date_time.strftime("%Y-%m-%d %H:%M:%S")),
                config="simple",
                weight="B",
            )
            for value in values
        ]
    return search_vectors


def search_products(qs, value):
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
