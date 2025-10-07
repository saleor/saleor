from unittest.mock import patch

from ..models import Page
from ..utils import mark_pages_search_vector_as_dirty_in_batches


@patch("saleor.page.utils.MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE", 1)
def test_mark_pages_search_vector_as_dirty_in_batches(page_list):
    # given
    page_ids = [page.id for page in page_list]
    Page.objects.all().update(search_index_dirty=False)

    # when
    mark_pages_search_vector_as_dirty_in_batches(page_ids)

    # then
    assert all(
        Page.objects.filter(id__in=page_ids).values_list(
            "search_index_dirty", flat=True
        )
    )
