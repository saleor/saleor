from typing import TYPE_CHECKING, Dict, Iterable, List, Union

from django.db import transaction
from ..models import Store, StoreType


if TYPE_CHECKING:
    # flake8: noqa
    from datetime import date, datetime

    from django.db.models.query import QuerySet

    from ...order.models import Order, OrderLine
    from ..models import Store


@transaction.atomic
def delete_stores(stores_ids: List[str]):
    """Delete stores and perform all necessary actions.

    Set products of deleted stores as unpublished.
    """
    stores = Store.objects.select_for_update().filter(pk__in=stores_ids)
    stores.delete()

@transaction.atomic
def delete_stores_types(stores_types_ids: List[str]):
    """Delete stores types and perform all necessary actions.

    Set products of deleted stores as unpublished.
    """
    storesTypes = StoreType.objects.select_for_update().filter(pk__in=stores_types_ids)
    storesTypes.delete()


