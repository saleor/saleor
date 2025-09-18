from unittest.mock import patch

from ..search import (
    update_pages_search_vector,
)


def test_update_pages_search_vector_multiple_pages(page_list):
    """Test updating search vector for multiple pages."""
    # given
    assert all(page.search_index_dirty for page in page_list)

    # when
    update_pages_search_vector([page.id for page in page_list])

    # then
    for page in page_list:
        page.refresh_from_db()
        assert page.search_vector is not None
        assert page.search_index_dirty is False


@patch("saleor.page.search.PAGE_BATCH_SIZE", 1)
def test_update_pages_search_vector_with_batch_size_one(page_list):
    """Test updating search vector with batch size of 1."""
    # given
    assert all(page.search_index_dirty for page in page_list)

    # when
    update_pages_search_vector([page.id for page in page_list])

    # then
    for page in page_list:
        page.refresh_from_db()
        assert page.search_vector is not None
        assert page.search_index_dirty is False


def test_update_pages_search_vector_empty_list(db):
    """Test updating search vector with empty page IDs list."""
    # given
    page_ids = []

    # when/then - should not raise any errors
    update_pages_search_vector(page_ids)


def test_update_pages_search_vector_nonexistent_pages(db):
    """Test updating search vector with non-existent page IDs."""
    # given
    page_ids = [99999, 88888]  # Non-existent IDs

    # when/then - should not raise any errors
    update_pages_search_vector(page_ids)
