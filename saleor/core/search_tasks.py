from celery.utils.log import get_task_logger

from ..account.search import prepare_user_search_document_value
from ..celeryconf import app
from ..order.search import prepare_order_search_document_value
from ..product.search import (
    PRODUCT_FIELDS_TO_PREFETCH,
    prepare_product_search_document_value,
)

task_logger = get_task_logger(__name__)

BATCH_SIZE = 10000


def set_user_search_document_values(total_count, updated_count, user_model):
    qs = user_model.objects.filter(search_document="").prefetch_related("addresses")[
        :BATCH_SIZE
    ]
    if not qs:
        task_logger.info("No users to update.")
        return

    set_search_document_all_values(
        qs,
        total_count,
        updated_count,
        prepare_user_search_document_value,
    )


def set_order_search_document_values(total_count, updated_count, order_model):
    qs = order_model.objects.filter(search_document="").prefetch_related(
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

    set_search_document_all_values(
        qs,
        total_count,
        updated_count,
        prepare_order_search_document_value,
    )


def set_product_search_document_values(total_count, updated_count, product_model):
    qs = product_model.objects.filter(search_document="").prefetch_related(
        *PRODUCT_FIELDS_TO_PREFETCH
    )[:BATCH_SIZE]
    if not qs:
        task_logger.info("No products to update.")
        return

    set_search_document_all_values(
        qs,
        total_count,
        updated_count,
        prepare_product_search_document_value,
    )


@app.task
def set_search_document_all_values(
    qs,
    total_count,
    updated_count,
    prepare_search_document_func,
    logger_msg,
):
    Model = qs.model
    updated_count = set_search_document_values(
        qs, total_count, updated_count, prepare_search_document_func
    )

    if updated_count == total_count:
        task_logger.info(
            f"Setting {Model.__name__.lower()} search document values finished.",
        )
        return

    return set_search_document_all_values.delay(
        qs, total_count, updated_count, prepare_search_document_func, logger_msg
    )


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
