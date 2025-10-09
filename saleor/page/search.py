from collections import defaultdict
from typing import NamedTuple

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import transaction
from django.db.models import F, Q, QuerySet, Value

from ..attribute.models import Attribute, AttributeValue
from ..attribute.search import get_search_vectors_for_attribute_values
from ..core.context import with_promise_context
from ..core.db.connection import allow_writer
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from ..core.utils.editorjs import clean_editor_js
from ..graphql.attribute.dataloaders.assigned_attributes import (
    AttributesByPageIdAndLimitLoader,
    AttributeValuesByPageIdAndAttributeIdAndLimitLoader,
)
from ..graphql.core.context import SaleorContext
from ..graphql.page.dataloaders import PageTypeByIdLoader
from .lock_objects import page_qs_select_for_update
from .models import Page, PageType


class AttributeValueData(NamedTuple):
    values: list[AttributeValue]
    attribute: Attribute | None


@allow_writer()
@with_promise_context
def update_pages_search_vector(
    pages: list[Page],
    page_id_to_title_map: dict[int, str] | None = None,
) -> None:
    """Update search vector for the given pages."""
    page_type_map, page_id_to_values_map, page_id_to_title_map = _load_page_data(pages)

    # Update search vector for each page
    for page in pages:
        page_type = page_type_map[page.page_type_id]
        values_data = page_id_to_values_map[page.id]
        page.search_vector = FlatConcatSearchVector(
            *prepare_page_search_vector_value(
                page, page_type, values_data, page_id_to_title_map
            )
        )
        page.search_index_dirty = False

    # Save updates
    with transaction.atomic():
        _locked_pages = (
            page_qs_select_for_update()
            .filter(id__in=[page.id for page in pages])
            .values_list("id", flat=True)
        )
        Page.objects.bulk_update(pages, ["search_vector", "search_index_dirty"])


def _load_page_data(
    pages: list[Page],
) -> tuple[dict[int, PageType], dict[int, list[AttributeValueData]], dict[int, str]]:
    """Load all required data for pages using dataloaders."""
    context = SaleorContext()
    page_ids = [page.id for page in pages]

    # Load page types
    page_types = (
        PageTypeByIdLoader(context)
        .load_many([page.page_type_id for page in pages])
        .get()
    )
    page_type_map = {pt.id: pt for pt in page_types if pt}

    # Load attributes and attribute values
    page_id_to_values_map, page_id_to_title_map = _load_attribute_data(
        context, page_ids
    )

    return page_type_map, page_id_to_values_map, page_id_to_title_map


def _load_attribute_data(
    context: SaleorContext, page_ids: list[int]
) -> tuple[dict[int, list[AttributeValueData]], dict[int, str]]:
    @with_promise_context
    def load_all_data():
        # Load attributes
        attributes_promise = AttributesByPageIdAndLimitLoader(context).load_many(
            [(page_id, settings.PAGE_MAX_INDEXED_ATTRIBUTES) for page_id in page_ids]
        )

        def with_attributes(attributes):
            # Build attribute map and queries
            attribute_map = {
                attr.id: attr for page_attrs in attributes for attr in page_attrs
            }

            page_id_attribute_id_with_limit = [
                (page_id, attribute.id, settings.PAGE_MAX_INDEXED_ATTRIBUTE_VALUES)
                for page_id, attrs in zip(page_ids, attributes, strict=True)
                for attribute in attrs[: settings.PAGE_MAX_INDEXED_ATTRIBUTES]
            ]

            # Load attribute values
            attribute_values_promise = (
                AttributeValuesByPageIdAndAttributeIdAndLimitLoader(context).load_many(
                    page_id_attribute_id_with_limit
                )
            )

            return attribute_values_promise.then(
                lambda attribute_values: (
                    attribute_map,
                    page_id_attribute_id_with_limit,
                    attribute_values,
                )
            )

        return attributes_promise.then(with_attributes)

    # Execute within Promise context
    attribute_map, page_id_attribute_id_with_limit, attribute_values = load_all_data()

    # Build page to values mapping
    page_id_to_values_map = defaultdict(list)
    value_ids = []
    for values, (page_id, attr_id, _) in zip(
        attribute_values, page_id_attribute_id_with_limit, strict=True
    ):
        attribute = attribute_map.get(attr_id)
        page_id_to_values_map[page_id].append(AttributeValueData(values, attribute))
        value_ids.extend([value.id for value in values])

    page_id_to_title_map = _get_page_to_title_map(value_ids)
    return page_id_to_values_map, page_id_to_title_map


def _get_page_to_title_map(value_ids: list[int]):
    db_conn = settings.DATABASE_CONNECTION_REPLICA_NAME
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
    return page_id_to_title_map


def prepare_page_search_vector_value(
    page: Page,
    page_type: PageType,
    values_data: list[AttributeValueData],
    page_id_to_title_map: dict[int, str],
) -> list[NoValidationSearchVector]:
    """Prepare the search vector value for a page."""
    search_vectors = [
        NoValidationSearchVector(Value(page.title), config="simple", weight="A"),
        NoValidationSearchVector(Value(page.slug), config="simple", weight="A"),
    ]
    if content := page.content:
        search_vectors += [
            NoValidationSearchVector(
                Value(clean_editor_js(content, to_string=True)),
                config="simple",
                weight="A",
            )
        ]

    # add page type data
    search_vectors.extend(
        [
            NoValidationSearchVector(
                Value(page_type.name), config="simple", weight="B"
            ),
            NoValidationSearchVector(
                Value(page_type.slug), config="simple", weight="B"
            ),
        ]
    )
    search_vectors.extend(
        generate_attributes_search_vector_value(
            values_data, page_id_to_title_map=page_id_to_title_map
        )
    )
    return search_vectors


def generate_attributes_search_vector_value(
    values_data: list[AttributeValueData],
    *,
    page_id_to_title_map: dict[int, str] | None = None,
) -> list[NoValidationSearchVector]:
    """Prepare `search_vector` value for assigned attributes.

    Method should receive assigned attributes with prefetched `values`
    """
    search_vectors = []

    for value_data in values_data:
        attribute = value_data.attribute
        values = value_data.values
        if not values or not attribute:
            continue
        search_vectors += get_search_vectors_for_attribute_values(
            attribute, values, page_id_to_title_map=page_id_to_title_map, weight="B"
        )
    return search_vectors


def search_pages(qs: QuerySet[Page], value: str) -> QuerySet[Page]:
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
