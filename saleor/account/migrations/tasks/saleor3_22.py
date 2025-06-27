from collections import defaultdict

from django.db import transaction

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ....order import OrderStatus
from ....order.models import Order
from ...models import User

BATCH_SIZE = 1000


@app.task
@allow_writer()
def populate_user_number_of_orders_task(user_pk=0):
    users = User.objects.filter(pk__gt=user_pk).order_by("pk")
    user_ids = list(users.values_list("id", flat=True)[:BATCH_SIZE])

    if not user_ids:
        return

    user_total_orders = defaultdict(int)
    orders = (
        Order.objects.exclude(status=OrderStatus.DRAFT)
        .filter(user_id__in=user_ids)
        .values("user_id", "id")
    )

    for order in orders:
        user_total_orders[order["user_id"]] += 1

    with transaction.atomic():
        users = (
            User.objects.filter(pk__in=user_ids)
            .order_by("pk")
            .select_for_update(of=(["self"]))
        )
        users_to_update = []
        for user in users:
            total_orders = user_total_orders.get(user.id, 0)

            # Skip if the total orders count is the same to avoid unnecessary updates
            if total_orders == user.number_of_orders:
                continue

            user.number_of_orders = total_orders
            users_to_update.append(user)

        User.objects.bulk_update(users_to_update, ["number_of_orders"])

    populate_user_number_of_orders_task.delay(user_ids[-1])
