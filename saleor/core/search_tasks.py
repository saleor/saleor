from celery.utils.log import get_task_logger

from ..account.models import User
from ..account.search import prepare_user_search_document_value
from ..celeryconf import app
from ..order.models import Order
from ..order.search import prepare_order_search_document_value

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
    users = []
    for user in qs:
        user.search_document = prepare_user_search_document_value(
            user, already_prefetched=True
        )
        users.append(user)
    User.objects.bulk_update(users, ["search_document"])

    updated_count += len(users)
    progress = round((updated_count / total_count) * 100, 2)

    task_logger.info(
        f"Updated {updated_count} from {total_count} users - {progress}% done."
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

    orders = []
    for order in qs:
        order.search_document = prepare_order_search_document_value(
            order, already_prefetched=True
        )
        orders.append(order)
    Order.objects.bulk_update(orders, ["search_document"])

    updated_count += len(orders)
    progress = round((updated_count / total_count) * 100, 2)

    task_logger.info(
        f"Updated {updated_count} from {total_count} orders - {progress}% done."
    )

    if updated_count == total_count:
        task_logger.info("Setting order search document values finished.")
        return

    return set_order_search_document_values.delay(total_count, updated_count)
