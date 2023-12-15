from django.conf import settings
from django.db.models import Exists, OuterRef

from ....celeryconf import app
from ....product.utils.variants import fetch_variants_for_promotion_rules
from ...models import (
    Promotion,
    PromotionRule,
)

# Results in update time ~0.4s and consumes ~20MB memory at peak
PROMOTION_RULE_BATCH_SIZE = 250


@app.task
def set_promotion_rule_variants(start_id=None):
    promotions = Promotion.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).active()
    kwargs = {"id__gt": start_id} if start_id else {}
    rules = (
        PromotionRule.objects.order_by("id")
        .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(Exists(promotions.filter(id=OuterRef("promotion_id"))), **kwargs)[
            :PROMOTION_RULE_BATCH_SIZE
        ]
    )
    if ids := list(rules.values_list("pk", flat=True)):
        qs = PromotionRule.objects.filter(pk__in=ids)
        fetch_variants_for_promotion_rules(rules=qs)
        set_promotion_rule_variants.delay(ids[-1])
