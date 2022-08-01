from typing import TYPE_CHECKING, List

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, Value, prefetch_related_objects

from ..attribute import AttributeInputType
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from ..core.utils.editorjs import clean_editor_js
from .models import Product

if TYPE_CHECKING:
    from django.db.models import QuerySet

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
            product.search_vector = FlatConcatSearchVector(
                *prepare_product_search_vector_value(product, already_prefetched=True)
            )

        Product.objects.bulk_update(products_batch, ["search_vector", "updated_at"])


def update_product_search_vector(product: "Product"):
    product.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product)
    )
    product.save(update_fields=["search_vector", "updated_at"])


def prepare_product_search_vector_value(
    product: "Product", *, already_prefetched=False
) -> List[NoValidationSearchVector]:
    if not already_prefetched:
        prefetch_related_objects([product], *PRODUCT_FIELDS_TO_PREFETCH)
    search_vectors = [
        NoValidationSearchVector(Value(product.name), config="simple", weight="A"),
        NoValidationSearchVector(
            Value(product.description_plaintext), config="simple", weight="C"
        ),
        *generate_attributes_search_vector_value(
            product.attributes.all()[: settings.PRODUCT_MAX_INDEXED_ATTRIBUTES]
        ),
        *generate_variants_search_vector_value(product),
    ]
    return search_vectors


def generate_variants_search_vector_value(
    product: "Product",
) -> List[NoValidationSearchVector]:
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
            search_vectors += generate_attributes_search_vector_value(
                variant.attributes.all()[: settings.PRODUCT_MAX_INDEXED_ATTRIBUTES]
            )
    return search_vectors


def generate_attributes_search_vector_value(
    assigned_attributes: "QuerySet",
) -> List[NoValidationSearchVector]:
    """Prepare `search_vector` value for assigned attributes.

    Method should receive assigned attributes with prefetched `values`
    and `assignment__attribute`.
    """
    search_vectors = []
    for assigned_attribute in assigned_attributes:
        attribute = assigned_attribute.assignment.attribute

        input_type = attribute.input_type
        values = assigned_attribute.values.all()[
            : settings.PRODUCT_MAX_INDEXED_ATTRIBUTE_VALUES
        ]
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
