from ....celeryconf import app
from ... import DiscountType
from ...models import CheckoutLineDiscount, OrderLineDiscount

ORDER_LINE_DISCOUNT_BATCH_SIZE = 250


@app.task
def update_discount_type_order_line_task():
    order_lines = OrderLineDiscount.objects.filter(type=DiscountType.PROMOTION)[
        :ORDER_LINE_DISCOUNT_BATCH_SIZE
    ]
    if not order_lines:
        return
    order_lines.update(type=DiscountType.CATALOGUE_PROMOTION)
    update_discount_type_order_line_task.delay()


@app.task
def update_discount_type_checkout_line_task():
    checkout_lines = CheckoutLineDiscount.objects.filter(type=DiscountType.PROMOTION)[
        :ORDER_LINE_DISCOUNT_BATCH_SIZE
    ]
    if not checkout_lines:
        return
    checkout_lines.update(type=DiscountType.CATALOGUE_PROMOTION)
    update_discount_type_checkout_line_task.delay()
