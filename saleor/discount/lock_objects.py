from django.db.models import QuerySet

from .models import PromotionRule


def promotion_rule_qs_select_for_update() -> QuerySet[PromotionRule]:
    return PromotionRule.objects.order_by("pk").select_for_update(of=["self"])
