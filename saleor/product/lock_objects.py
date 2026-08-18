from django.db.models import QuerySet

from ..core.db.locks import AdvisoryLock, acquire_advisory_xact_lock
from .models import Category, Product


def product_qs_select_for_update() -> QuerySet[Product]:
    return Product.objects.order_by("pk").select_for_update(of=(["self"]))


def category_qs_select_for_update() -> QuerySet[Category]:
    return Category.objects.order_by("pk").select_for_update(of=["self"])


def acquire_category_tree_lock(using: str | None = None) -> None:
    """Serialize structural writes to the Category MPTT tree.

    Acquire inside an atomic block before any insert, delete, or rebuild -
    mptt's lft/rght renumbering races under concurrency.
    """
    acquire_advisory_xact_lock(AdvisoryLock.CATEGORY_TREE, using=using)
