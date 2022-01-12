from celery.utils.log import get_task_logger

from ..account.models import User
from ..account.search import prepare_user_search_document_value
from ..celeryconf import app
from ..order.models import Order
from ..order.search import prepare_order_search_document_value
from ..product.models import Product
from ..product.search import (
    PRODUCT_FIELDS_TO_PREFETCH,
    prepare_product_search_document_value,
)

task_logger = get_task_logger(__name__)

BATCH_SIZE = 10000


@app.task
def set_user_search_document_values(total_count, updated_count):
    qs = User.objects.filter(search_document="").prefetch_related("addresses")[
        :BATCH_SIZE
    ]
    if not qs:
        task_logger.info("No users to update.")
        return

    updated_count = set_search_document_values(
        qs, total_count, updated_count, prepare_user_search_document_value
    )

    if updated_count == total_count:
        task_logger.info("Setting user search document values finished.")
        return

    return set_user_search_document_values.delay(total_count, updated_count)


@app.task
def set_order_search_document_values(total_count, updated_count):
    qs = Order.objects.filter(search_document="").prefetch_related(
        "user",
        "billing_address",
        "shipping_address",
        "payments",
        "discounts",
        "lines",
    )[:BATCH_SIZE]
    if not qs:
        task_logger.info("No orders to update.")
        return

    updated_count = set_search_document_values(
        qs, total_count, updated_count, prepare_order_search_document_value
    )

    if updated_count == total_count:
        task_logger.info("Setting order search document values finished.")
        return

    return set_order_search_document_values.delay(total_count, updated_count)


@app.task
def set_product_search_document_values(total_count, updated_count):
    qs = Product.objects.filter(search_document="").prefetch_related(
        *PRODUCT_FIELDS_TO_PREFETCH
    )[:BATCH_SIZE]
    if not qs:
        task_logger.info("No products to update.")
        return

    updated_count = set_search_document_values(
        qs, total_count, updated_count, prepare_product_search_document_value
    )

    if updated_count == total_count:
        task_logger.info("Setting product search document values finished.")
        return

    return set_product_search_document_values.delay(total_count, updated_count)


def set_search_document_values(
    qs, total_count, updated_count, prepare_search_document_func
):
    Model = qs.model
    instances = []
    for instance in qs:
        instance.search_document = prepare_search_document_func(
            instance, already_prefetched=True
        )
        instances.append(instance)
    Model.objects.bulk_update(instances, ["search_document"])

    updated_count += len(instances)
    progress = round((updated_count / total_count) * 100, 2)

    task_logger.info(
        f"Updated {updated_count} from {total_count} {Model.__name__.lower()}s - "
        f"{progress}% done."
    )
    return updated_count
