from .tasks import mark_pages_search_vector_as_dirty

# Results in update time ~0.2s, consumes ~30 MB
MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE = 1000


def mark_pages_search_vector_as_dirty_in_batches(page_ids: list[int]):
    """Mark pages as needing search index updates."""
    for i in range(0, len(page_ids), MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE):
        batch_ids = page_ids[i : i + MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE]
        mark_pages_search_vector_as_dirty.delay(batch_ids)
