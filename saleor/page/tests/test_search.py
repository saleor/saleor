from ..search import (
    update_pages_search_vector,
)


def test_update_pages_search_vector_multiple_pages(page_list):
    """Test updating search vector for multiple pages."""
    # given
    assert all(page.search_index_dirty for page in page_list)

    # when
    update_pages_search_vector(page_list)

    # then
    for page in page_list:
        page.refresh_from_db()
        assert page.search_vector is not None
        assert page.search_index_dirty is False


def test_update_pages_search_vector_empty_list(db):
    """Test updating search vector with empty page IDs list."""
    # given
    pages = []

    # when/then - should not raise any errors
    update_pages_search_vector(pages)
