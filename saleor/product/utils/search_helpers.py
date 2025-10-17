from ..tasks import mark_products_search_vector_as_dirty

# Results in update time ~0.2s, consumes ~30 MB
MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE = 1000


def mark_products_search_vector_as_dirty_in_batches(product_ids: list[int]):
    """Mark products as needing search index updates."""
    for i in range(0, len(product_ids), MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE):
        batch_ids = product_ids[i : i + MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE]
        mark_products_search_vector_as_dirty.delay(batch_ids)
