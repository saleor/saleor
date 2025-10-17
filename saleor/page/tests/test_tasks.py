from unittest.mock import patch

from ..models import Page
from ..tasks import mark_pages_search_vector_as_dirty, update_pages_search_vector_task


@patch("saleor.page.tasks.update_pages_search_vector")
def test_update_pages_search_vector(update_pages_search_vector_mock, page_list):
    """Test updating search vector with batch size of 1."""
    # given
    assert all(page.search_index_dirty for page in page_list)

    # when
    update_pages_search_vector_task()

    # then
    assert update_pages_search_vector_mock.called


@patch("saleor.page.tasks.update_pages_search_vector")
def test_update_pages_search_vector_nothing_to_update(
    update_pages_search_vector_mock, page_list
):
    """Test updating search vector with batch size of 1."""
    # given
    Page.objects.all().update(search_index_dirty=False)

    # when
    update_pages_search_vector_task()

    # then
    assert not update_pages_search_vector_mock.called


def test_mark_pages_search_vector_as_dirty(page_list):
    # given
    page_ids = [page.id for page in page_list]
    Page.objects.all().update(search_index_dirty=False)

    # when
    mark_pages_search_vector_as_dirty(page_ids)

    # then
    assert all(
        Page.objects.filter(id__in=page_ids).values_list(
            "search_index_dirty", flat=True
        )
    )
