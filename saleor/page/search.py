from collections import defaultdict
from collections.abc import Iterable

from django.conf import settings
from django.db import transaction
from django.db.models import Value, prefetch_related_objects

from ..attribute.models import AssignedPageAttributeValue, AttributeValue
from ..attribute.search import get_search_vectors_for_attribute_values
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from ..core.utils.editorjs import clean_editor_js
from .lock_objects import page_qs_select_for_update
from .models import Page

PAGE_FIELDS_TO_PREFETCH = [
    "page_type__attributepage__attribute",
    "attributevalues__value",
]
PAGE_BATCH_SIZE = 100


def update_pages_search_vector(page_ids: Iterable[int]):
    db_conn = settings.DATABASE_CONNECTION_REPLICA_NAME
    page_ids = list(page_ids)
    pages = Page.objects.using(db_conn).filter(pk__in=page_ids).order_by("pk")
    for page_pks in queryset_in_batches(pages):
        value_ids = (
            AssignedPageAttributeValue.objects.using(db_conn)
            .filter(page_id__in=page_pks)
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

        pages_batch = list(Page.objects.using(db_conn).filter(id__in=page_pks))
        _prepare_pages_search_vector_index(pages_batch, page_id_to_title_map)


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:PAGE_BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


def _prepare_pages_search_vector_index(
    pages: list[Page],
    page_id_to_title_map: dict[int, str] | None = None,
) -> None:
    prefetch_related_objects(pages, *PAGE_FIELDS_TO_PREFETCH)

    for page in pages:
        page.search_vector = FlatConcatSearchVector(
            *prepare_page_search_vector_value(page, page_id_to_title_map)
        )
        page.search_index_dirty = False

    with transaction.atomic():
        _locked_pages = (
            page_qs_select_for_update()
            .filter(id__in=[page.id for page in pages])
            .values_list("id", flat=True)
        )
        Page.objects.bulk_update(pages, ["search_vector", "search_index_dirty"])


def prepare_page_search_vector_value(
    page: Page, page_id_to_title_map: dict[int, str] | None = None
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
                Value(page.page_type.name), config="simple", weight="B"
            ),
            NoValidationSearchVector(
                Value(page.page_type.slug), config="simple", weight="B"
            ),
        ]
    )
    search_vectors.extend(
        generate_attributes_search_vector_value(
            page, page_id_to_title_map=page_id_to_title_map
        )
    )
    return search_vectors


def generate_attributes_search_vector_value(
    page: "Page",
    *,
    page_id_to_title_map: dict[int, str] | None = None,
) -> list[NoValidationSearchVector]:
    """Prepare `search_vector` value for assigned attributes.

    Method should receive assigned attributes with prefetched `values`
    """
    page_attributes = page.page_type.attributepage.all()

    attributes = [page_attribute.attribute for page_attribute in page_attributes][
        : settings.PAGE_MAX_INDEXED_ATTRIBUTES
    ]

    assigned_values = page.attributevalues.all()

    search_vectors = []

    values_map = defaultdict(list)
    for assigned_value in assigned_values:
        value = assigned_value.value
        values_map[value.attribute_id].append(value)

    for attribute in attributes:
        values = values_map[attribute.pk][: settings.PAGE_MAX_INDEXED_ATTRIBUTE_VALUES]

        search_vectors += get_search_vectors_for_attribute_values(
            attribute, values, page_id_to_title_map=page_id_to_title_map, weight="B"
        )
    return search_vectors
