from functools import reduce
from operator import add
from typing import TYPE_CHECKING, Optional, Union

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F, Q, Value, prefetch_related_objects

from ..attribute import AttributeInputType
from ..core.utils.editorjs import clean_editor_js
from .models import Product

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ..attribute.models import AssignedProductAttribute, AssignedVariantAttribute

ASSIGNED_ATTRIBUTE_TYPE = Union["AssignedProductAttribute", "AssignedVariantAttribute"]

PRODUCT_SEARCH_FIELDS = ["name", "description_plaintext"]
PRODUCT_FIELDS_TO_PREFETCH = [
    "variants__attributes__values",
    "variants__attributes__assignment__attribute",
    "attributes__values",
    "attributes__assignment__attribute",
]

PRODUCTS_BATCH_SIZE = 300
# Setting threshold to 300 results in about 350MB of memory usage
# when testing locally. Should be adjusted after some time by running
# update task on a large dataset and measureing the total time, memory usage
# and time of a single SQL statement.


def update_products_search_vector(products: "QuerySet"):
    last_id = 0
    while True:
        products_batch = list(
            products.order_by("id").filter(id__gt=last_id)[:PRODUCTS_BATCH_SIZE]
        )
        if not products_batch:
            break
        last_id = products_batch[-1].id

        prefetch_related_objects(products_batch, *PRODUCT_FIELDS_TO_PREFETCH)
        for product in products_batch:
            product.search_vector = prepare_product_search_vector_value(
                product, already_prefetched=True
            )

        Product.objects.bulk_update(products_batch, ["search_vector", "updated_at"])


def update_product_search_vector(product: "Product"):
    product.search_vector = prepare_product_search_vector_value(product)
    product.save(update_fields=["search_vector", "updated_at"])


def prepare_product_search_vector_value(
    product: "Product", *, already_prefetched=False
) -> SearchVector:
    if not already_prefetched:
        prefetch_related_objects([product], *PRODUCT_FIELDS_TO_PREFETCH)
    search_vector = SearchVector(
        Value(product.name), config="simple", weight="A"
    ) + SearchVector(Value(product.description_plaintext), config="simple", weight="C")
    attributes_vector = generate_attributes_search_vector_value(
        product.attributes.all()
    )
    if attributes_vector:
        search_vector += attributes_vector
    variants_vector = generate_variants_search_vector_value(product)
    if variants_vector:
        search_vector += variants_vector

    return search_vector


def generate_variants_search_vector_value(product: "Product") -> Optional[SearchVector]:
    variants = list(product.variants.all())

    variant_vectors = [
        SearchVector(
            Value(variant.sku), Value(variant.name), config="simple", weight="A"
        )
        if variant.sku
        else SearchVector(Value(variant.name), config="simple", weight="A")
        for variant in variants
        if variant.sku or variant.name
    ]

    if not variant_vectors:
        return None

    search_vector = reduce(add, variant_vectors)

    for variant in variants:
        attribute_vector = generate_attributes_search_vector_value(
            variant.attributes.all()
        )
        if attribute_vector:
            search_vector += attribute_vector

    return search_vector


def generate_attributes_search_vector_value(
    assigned_attributes: "QuerySet",
) -> Optional[SearchVector]:
    """Prepare `search_vector` value for assigned attributes.

    Method should received assigned attributes with prefetched `values`
    and `assignment__attribute`.
    """
    search_vector = None
    for assigned_attribute in assigned_attributes:
        attribute = assigned_attribute.assignment.attribute

        input_type = attribute.input_type
        values = assigned_attribute.values.all()
        values_list = []
        if input_type in [AttributeInputType.DROPDOWN, AttributeInputType.MULTISELECT]:
            values_list = [value.name for value in values]
        elif input_type == AttributeInputType.RICH_TEXT:
            values_list = [
                clean_editor_js(value.rich_text, to_string=True) for value in values
            ]
        elif input_type == AttributeInputType.PLAIN_TEXT:
            values_list = [value.plain_text for value in values]
        elif input_type == AttributeInputType.NUMERIC:
            unit = attribute.unit
            values_list = [
                value.name + " " + unit if unit else value.name for value in values
            ]
        elif input_type in [AttributeInputType.DATE, AttributeInputType.DATE_TIME]:
            values_list = [
                value.date_time.strftime("%Y-%m-%d %H:%M:%S") for value in values
            ]

        if values_list:
            new_vector = reduce(
                add,
                (
                    SearchVector(Value(v), config="simple", weight="B")
                    for v in values_list
                ),
            )
            if search_vector is not None:
                search_vector += new_vector
            else:
                search_vector = new_vector
    return search_vector


def search_products(qs, value):
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
