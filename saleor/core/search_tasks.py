from typing import Any

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction

from ..account.models import User
from ..account.search import prepare_user_search_document_value
from ..celeryconf import app
from ..core.db.connection import allow_writer
from ..order.models import Order
from ..order.search import prepare_order_search_vector_value
from ..product.models import Product
from ..product.search import (
    PRODUCT_FIELDS_TO_PREFETCH,
    prepare_product_search_vector_value,
)
from .postgres import FlatConcatSearchVector

task_logger = get_task_logger(__name__)

ORDER_BATCH_SIZE = 100

BATCH_SIZE = 500
# Based on local testing, 500 should be a good balance between performance
# total time and memory usage. Should be tested after some time and adjusted by
# running the task on different thresholds and measure memory usage, total time
# and execution time of a single SQL statement.


@app.task
def set_user_search_document_values(updated_count: int = 0) -> None:
    users = list(
        User.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(search_document="")
        .prefetch_related("addresses")
        .order_by("-id")[:BATCH_SIZE]
    )

    if not users:
        task_logger.info("No users to update.")
        return

    with allow_writer():
        updated_count += set_search_document_values(
            users, prepare_user_search_document_value
        )

    task_logger.info("Updated %d users", updated_count)

    if len(users) < BATCH_SIZE:
        task_logger.info("Setting user search document values finished.")
        return

    del users

    set_user_search_document_values.delay(updated_count)


@app.task
def set_order_search_document_values(
    update_all: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_REPLICA_NAME,
    updated_count: int = 0,
    order_number: int = 0,
) -> None:
    """Update search document values for orders.

    If `update_all` is False, it will update only orders with search_vector=None.
    """
    lookup: dict[str, Any] = {"number__gte": order_number}
    if not update_all:
        lookup["search_vector"] = None

    orders_qs = (
        Order.objects.using(database_connection_name)
        .filter(**lookup)
        .order_by("number")
    )

    numbers = list(orders_qs.values_list("number", flat=True)[:ORDER_BATCH_SIZE])
    if not numbers:
        task_logger.info("No orders to update.")
        return

    with allow_writer():
        orders = (
            Order.objects.filter(number__in=numbers)
            .prefetch_related(
                "user",
                "billing_address",
                "shipping_address",
                "payments",
                "discounts",
                "lines",
                "payment_transactions__events",
                "invoices",
                "events",
            )
            .order_by("pk")
        )
        with transaction.atomic():
            _orders_lock = list(orders.select_for_update(of=(["self"])))
            updated_count += set_search_vector_values(
                list(orders), prepare_order_search_vector_value
            )

    task_logger.info("Updated %d orders", updated_count)

    if len(numbers) < ORDER_BATCH_SIZE:
        task_logger.info("Setting order search document values finished.")
        return

    del orders

    set_order_search_document_values.delay(
        update_all, database_connection_name, updated_count, order_number=numbers[-1]
    )


@app.task
def set_product_search_document_values(updated_count: int = 0) -> None:
    products = list(
        Product.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(search_vector=None)
        .prefetch_related(*PRODUCT_FIELDS_TO_PREFETCH)
        .order_by("-id")[:BATCH_SIZE]
    )

    if not products:
        task_logger.info("No products to update.")
        return

    with allow_writer():
        updated_count += set_search_vector_values(
            products,
            prepare_product_search_vector_value,
        )

    task_logger.info("Updated %d products", updated_count)

    if len(products) < BATCH_SIZE:
        task_logger.info("Setting product search document values finished.")
        return

    del products

    set_product_search_document_values.delay(updated_count)


def set_search_document_values(instances: list, prepare_search_document_func):
    if not instances:
        return 0
    Model = instances[0]._meta.model
    for instance in instances:
        instance.search_document = prepare_search_document_func(
            instance, already_prefetched=True
        )
    Model.objects.bulk_update(instances, ["search_document"])

    return len(instances)


def set_search_vector_values(
    instances,
    prepare_search_vector_func,
):
    Model = instances[0]._meta.model
    for instance in instances:
        instance.search_vector = FlatConcatSearchVector(
            *prepare_search_vector_func(instance, already_prefetched=True)
        )
    Model.objects.bulk_update(instances, ["search_vector"])

    return len(instances)
