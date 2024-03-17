from ....celeryconf import app
from ... import DiscountType
from ...models import OrderLineDiscount

ORDER_LINE_DISCOUNT_BATCH_SIZE = 100


@app.task
def set_discount_type_to_promotion_catalogue_task():
    lines = OrderLineDiscount.objects.filter(type=DiscountType.PROMOTION)[
        :ORDER_LINE_DISCOUNT_BATCH_SIZE
    ]
    if not lines:
        return
    lines.update(type=DiscountType.CATALOGUE_PROMOTION)
    set_discount_type_to_promotion_catalogue_task.delay()
