from collections import defaultdict
from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, Value, prefetch_related_objects

from ..attribute.models import AssignedProductAttributeValue, AttributeValue
from ..attribute.search import get_search_vectors_for_attribute_values
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from ..core.utils.batches import queryset_in_batches
from ..page.models import Page
from ..product.models import Product

if TYPE_CHECKING:
    from django.db.models import QuerySet

PRODUCT_SEARCH_FIELDS = ["name", "description_plaintext"]
PRODUCT_FIELDS_TO_PREFETCH = [
    "variants__attributes__values",
    "variants__attributes__assignment__attribute",
    "attributevalues__value",
    "product_type__attributeproduct__attribute",
]

PRODUCTS_BATCH_SIZE = 100
# Setting threshold to 100 results in about 766.98MB of memory usage
# when testing locally with multiple attributes of different types assigned to product
# and product variants.


def _prep_product_search_vector_index(
    products, page_id_to_title_map: dict[int, str] | None = None
):
    prefetch_related_objects(products, *PRODUCT_FIELDS_TO_PREFETCH)

    for product in products:
        product.search_vector = FlatConcatSearchVector(
            *prepare_product_search_vector_value(
                product,
                already_prefetched=True,
                page_id_to_title_map=page_id_to_title_map,
            )
        )
        product.search_index_dirty = False

    Product.objects.bulk_update(
        products, ["search_vector", "updated_at", "search_index_dirty"]
    )


def update_products_search_vector(product_ids: Iterable[int]):
    db_conn = settings.DATABASE_CONNECTION_REPLICA_NAME
    product_ids = list(product_ids)
    products = Product.objects.using(db_conn).filter(pk__in=product_ids).order_by("pk")
    for product_pks in queryset_in_batches(products, PRODUCTS_BATCH_SIZE):
        value_ids = (
            AssignedProductAttributeValue.objects.using(db_conn)
            .filter(product_id__in=product_pks)
            .values_list("value_id", flat=True)
        )
        value_to_page_id = (
            AttributeValue.objects.using(db_conn)
            .filter(id__in=value_ids, reference_page_id__isnull=False)
            .values_list("id", "reference_page_id")
        )
        page_id_to_title_map = dict(
            Page.objects.using(db_conn)
            .filter(id__in=[page_id for _, page_id in value_to_page_id])
            .values_list("id", "title")
        )

        products_batch = list(Product.objects.using(db_conn).filter(id__in=product_pks))
        _prep_product_search_vector_index(products_batch, page_id_to_title_map)


def prepare_product_search_vector_value(
    product: "Product",
    *,
    already_prefetched=False,
    page_id_to_title_map: dict[int, str] | None = None,
) -> list[NoValidationSearchVector]:
    if not already_prefetched:
        prefetch_related_objects([product], *PRODUCT_FIELDS_TO_PREFETCH)

    search_vectors = [
        NoValidationSearchVector(Value(product.name), config="simple", weight="A"),
        NoValidationSearchVector(
            Value(product.description_plaintext), config="simple", weight="C"
        ),
        *generate_attributes_search_vector_value(
            product, page_id_to_title_map=page_id_to_title_map
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
    *,
    page_id_to_title_map: dict[int, str] | None = None,
) -> list[NoValidationSearchVector]:
    """Prepare `search_vector` value for assigned attributes.

    Method should receive assigned attributes with prefetched `values`
    """
    product_attributes = product.product_type.attributeproduct.all()

    attributes = [
        product_attribute.attribute for product_attribute in product_attributes
    ][: settings.PRODUCT_MAX_INDEXED_ATTRIBUTES]

    assigned_values = product.attributevalues.all()

    search_vectors = []

    values_map = defaultdict(list)
    for av in assigned_values:
        values_map[av.value.attribute_id].append(av.value)

    for attribute in attributes:
        values = values_map[attribute.pk][
            : settings.PRODUCT_MAX_INDEXED_ATTRIBUTE_VALUES
        ]

        search_vectors += get_search_vectors_for_attribute_values(
            attribute, values, page_id_to_title_map=page_id_to_title_map, weight="B"
        )
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
        search_vectors += get_search_vectors_for_attribute_values(
            attribute, values, weight="B"
        )
    return search_vectors


def search_products(qs, value):
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
