from ..core.db.locks import AdvisoryLock, acquire_advisory_xact_lock


def acquire_menu_item_tree_lock(using: str | None = None) -> None:
    """Serialize structural writes to the MenuItem MPTT tree.

    Acquire inside an atomic block before any insert, parent change, delete,
    or rebuild - mptt's lft/rght renumbering races under concurrency.
    """
    acquire_advisory_xact_lock(AdvisoryLock.MENU_ITEM_TREE, using=using)
