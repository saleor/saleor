from django.db import transaction

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ....product.models import Product, ProductVariant
from ...models import OrderLine

ORDER_LINE_PRODUCT_ID_BATCH_SIZE = 250


@app.task
@allow_writer()
def populate_order_line_product_type_id_task(line_pk=None):
    """Populate product id for order lines."""
    if line_pk is None:
        line_pk = 0
    lines = OrderLine.objects.filter(
        pk__gte=line_pk, variant__isnull=False, product_type_id__isnull=True
    )
    qs = lines.order_by("pk")

    line_id_with_variant_id = qs.values_list("pk", "variant_id")[
        :ORDER_LINE_PRODUCT_ID_BATCH_SIZE
    ]

    variant_id_to_product_id = dict(
        ProductVariant.objects.filter(
            pk__in=[variant_id for _, variant_id in line_id_with_variant_id]
        ).values_list("id", "product_id")
    )

    product_id_to_product_type_id_map = dict(
        Product.objects.filter(pk__in=variant_id_to_product_id.values()).values_list(
            "id", "product_type_id"
        )
    )
    variant_id_to_product_type_id = {
        variant_id: product_id_to_product_type_id_map[product_id]
        for variant_id, product_id in variant_id_to_product_id.items()
    }

    line_pks = [line_id for (line_id, _) in line_id_with_variant_id]
    if line_pks:
        lines = OrderLine.objects.filter(pk__in=line_pks).order_by("pk")
        with transaction.atomic():
            to_save = []
            _lines_lock = list(lines.select_for_update(of=(["self"])))
            for line in lines:
                product_type_id = variant_id_to_product_type_id.get(line.variant_id)
                if not product_type_id:
                    continue
                line.product_type_id = product_type_id
                to_save.append(line)
            OrderLine.objects.bulk_update(to_save, ["product_type_id"])
        populate_order_line_product_type_id_task.delay(line_pks[-1])
