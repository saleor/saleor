from django.db.models import Subquery, OuterRef, Max

from ...models import Attribute, AttributeValue
from ....celeryconf import app


@app.task()
def setup_max_sort_order():
    Attribute.objects.filter(max_sort_order=None).update(
        max_sort_order=Subquery(
            AttributeValue.objects.filter(attribute_id=OuterRef("pk"))
            .order_by()
            .values("attribute_id")
            .annotate(max_sort_order=Max("sort_order"))
            .values("max_sort_order")
        )
    )
