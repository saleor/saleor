from typing import Optional

import graphene

from ..account.models import User
from ..app.models import App
from . import PromotionEvents
from .models import Promotion, PromotionEvent, PromotionRule


def _promotion_base_event(
    promotion: Promotion,
    user: Optional[User],
    app: Optional[App],
    type: str,
):
    return PromotionEvent.objects.create(
        promotion=promotion, user=user, app=app, type=type
    )


def promotion_created_event(
    promotion: Promotion, user: Optional[User], app: Optional[App]
):
    return _promotion_base_event(
        promotion=promotion, user=user, app=app, type=PromotionEvents.PROMOTION_CREATED
    )


def promotion_updated_event(
    promotion: Promotion, user: Optional[User], app: Optional[App]
):
    return _promotion_base_event(
        promotion=promotion, user=user, app=app, type=PromotionEvents.PROMOTION_UPDATED
    )


def promotion_started_event(
    promotion: Promotion, user: Optional[User], app: Optional[App]
):
    return _promotion_base_event(
        promotion=promotion, user=user, app=app, type=PromotionEvents.PROMOTION_STARTED
    )


def promotion_ended_event(
    promotion: Promotion, user: Optional[User], app: Optional[App]
):
    return _promotion_base_event(
        promotion=promotion, user=user, app=app, type=PromotionEvents.PROMOTION_ENDED
    )


def _rule_base_event(
    user: Optional[User],
    app: Optional[App],
    rules: list[PromotionRule],
    type: str,
):
    events = []
    for rule in rules:
        events.append(
            PromotionEvent(
                promotion=rule.promotion,
                type=type,
                user=user,
                app=app,
                parameters={
                    "rule_id": graphene.Node.to_global_id("PromotionRule", rule.id)
                },
            )
        )
    return PromotionEvent.objects.bulk_create(events)


def rule_created_event(
    user: Optional[User],
    app: Optional[App],
    rules: list[PromotionRule],
):
    return _rule_base_event(
        user=user,
        app=app,
        rules=rules,
        type=PromotionEvents.RULE_CREATED,
    )


def rule_updated_event(
    user: Optional[User],
    app: Optional[App],
    rules: list[PromotionRule],
):
    return _rule_base_event(
        user=user,
        app=app,
        rules=rules,
        type=PromotionEvents.RULE_UPDATED,
    )


def rule_deleted_event(
    user: Optional[User],
    app: Optional[App],
    rules: list[PromotionRule],
):
    return _rule_base_event(
        user=user,
        app=app,
        rules=rules,
        type=PromotionEvents.RULE_DELETED,
    )
