import graphene
from graphene import relay

from ....discount import PromotionEvents as events
from ....discount import models
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AccountPermissions, AppPermission
from ...account.dataloaders import UserByUserIdLoader
from ...account.utils import is_owner_or_has_one_of_perms
from ...app.dataloaders import AppByIdLoader
from ...core.descriptions import ADDED_IN_317, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.fields import PermissionsField
from ...core.scalars import DateTime
from ...core.types import ModelObjectType
from ...core.types.user_or_app import UserOrApp
from ...utils import get_user_or_app_from_context
from ..enums import PromotionEventsEnum


def resolve_event_type(root: models.PromotionEvent, _info):
    return root.type


class PromotionEventInterface(graphene.Interface):
    id = graphene.GlobalID()
    date = DateTime(description="Date when event happened.", required=True)
    type = PromotionEventsEnum(
        description="Promotion event type.", resolver=resolve_event_type, required=True
    )
    created_by = PermissionsField(
        UserOrApp,
        description="User or App that created the promotion event. ",
        permissions=[
            AccountPermissions.MANAGE_STAFF,
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.OWNER,
        ],
    )

    class Meta:
        model = models.PromotionEvent

    @staticmethod
    def resolve_type(instance: models.PromotionEvent, _info):
        return PROMOTION_EVENT_MAP.get(instance.type)

    @staticmethod
    def resolve_created_by(root: models.PromotionEvent, info):
        requester = get_user_or_app_from_context(info.context)
        if not requester:
            return None

        def _resolve_user(user):
            if is_owner_or_has_one_of_perms(
                requester,
                user,
                AccountPermissions.MANAGE_STAFF,
            ):
                return user
            return None

        def _resolve_app(app):
            if is_owner_or_has_one_of_perms(
                requester,
                app,
                AppPermission.MANAGE_APPS,
            ):
                return app
            return None

        if root.user_id:
            return (
                UserByUserIdLoader(info.context).load(root.user_id).then(_resolve_user)
            )
        if root.app_id:
            return AppByIdLoader(info.context).load(root.app_id).then(_resolve_app)

        return None


class PromotionCreatedEvent(ModelObjectType[models.PromotionEvent]):
    class Meta:
        description = (
            "History log of the promotion created event."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, PromotionEventInterface]
        model = models.PromotionEvent
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionUpdatedEvent(ModelObjectType[models.PromotionEvent]):
    class Meta:
        description = (
            "History log of the promotion updated event."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, PromotionEventInterface]
        model = models.PromotionEvent
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionStartedEvent(ModelObjectType[models.PromotionEvent]):
    class Meta:
        description = (
            "History log of the promotion started event."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, PromotionEventInterface]
        model = models.PromotionEvent
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionEndedEvent(ModelObjectType[models.PromotionEvent]):
    class Meta:
        description = (
            "History log of the promotion ended event." + ADDED_IN_317 + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, PromotionEventInterface]
        model = models.PromotionEvent
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionRuleEventInterface(graphene.Interface):
    class Meta:
        description = (
            "History log of the promotion event related to rule."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = [relay.Node]
        model = models.PromotionEvent
        doc_category = DOC_CATEGORY_DISCOUNTS

    rule_id = graphene.String(
        description="The rule ID associated with the promotion event."
    )

    @staticmethod
    def resolve_rule_id(root: models.PromotionEvent, _info):
        return root.parameters.get("rule_id", None)


class PromotionRuleCreatedEvent(ModelObjectType[models.PromotionEvent]):
    class Meta:
        description = (
            "History log of the promotion rule created event."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, PromotionEventInterface, PromotionRuleEventInterface]
        model = models.PromotionEvent
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionRuleUpdatedEvent(ModelObjectType[models.PromotionEvent]):
    class Meta:
        description = (
            "History log of the promotion rule created event."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, PromotionEventInterface, PromotionRuleEventInterface]
        model = models.PromotionEvent
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionRuleDeletedEvent(ModelObjectType[models.PromotionEvent]):
    class Meta:
        description = (
            "History log of the promotion rule created event."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, PromotionEventInterface, PromotionRuleEventInterface]
        model = models.PromotionEvent
        doc_category = DOC_CATEGORY_DISCOUNTS


PROMOTION_EVENT_MAP = {
    events.PROMOTION_CREATED: PromotionCreatedEvent,
    events.PROMOTION_UPDATED: PromotionUpdatedEvent,
    events.PROMOTION_STARTED: PromotionStartedEvent,
    events.PROMOTION_ENDED: PromotionEndedEvent,
    events.RULE_CREATED: PromotionRuleCreatedEvent,
    events.RULE_UPDATED: PromotionRuleUpdatedEvent,
    events.RULE_DELETED: PromotionRuleDeletedEvent,
}


class PromotionEvent(graphene.Union):
    class Meta:
        types = [v for v in PROMOTION_EVENT_MAP.values()]

    @classmethod
    def resolve_type(cls, instance: models.PromotionEvent, _info):
        return PROMOTION_EVENT_MAP.get(instance.type)
