import graphene
from graphene import relay

from ....discount import models
from ....permission.auth_filters import AuthorizationFilters
from ...channel.types import Channel
from ...core import ResolveInfo
from ...core.connection import CountableConnection
from ...core.descriptions import ADDED_IN_317, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.fields import PermissionsField
from ...core.scalars import JSON, PositiveDecimal
from ...core.types import ModelObjectType, NonNullList
from ...meta.types import ObjectWithMetadata
from ...translations.fields import TranslationField
from ...translations.types import PromotionRuleTranslation, PromotionTranslation
from ..dataloaders import (
    ChannelsByPromotionRuleIdLoader,
    PromotionByIdLoader,
    PromotionEventsByPromotionIdLoader,
    PromotionRulesByPromotionIdLoader,
)
from ..enums import RewardValueTypeEnum
from .promotion_events import PromotionEvent


class Promotion(ModelObjectType[models.Promotion]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True, description="Name of the promotion.")
    description = JSON(description="Description of the promotion.")
    start_date = graphene.DateTime(
        required=True, description="Start date of the promotion."
    )
    end_date = graphene.DateTime(description="End date of the promotion.")
    created_at = graphene.DateTime(
        required=True, description="Date time of promotion creation."
    )
    updated_at = graphene.DateTime(
        required=True, description="Date time of last update of promotion."
    )
    rules = NonNullList(
        lambda: PromotionRule, description="The list of promotion rules."
    )
    translation = TranslationField(PromotionTranslation, type_name="promotion")
    events = NonNullList(
        PromotionEvent,
        description="The list of events associated with the promotion.",
    )

    class Meta:
        description = (
            "Represents the promotion that allow creating discounts based on given "
            "conditions, and is visible to all the customers."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Promotion
        doc_category = DOC_CATEGORY_DISCOUNTS

    @staticmethod
    def resolve_rules(root: models.Promotion, info: ResolveInfo):
        return PromotionRulesByPromotionIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_events(root: models.Promotion, info: ResolveInfo):
        return PromotionEventsByPromotionIdLoader(info.context).load(root.id)


class PromotionRule(ModelObjectType[models.PromotionRule]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(description="Name of the promotion rule.")
    description = JSON(description="Description of the promotion rule.")
    promotion = graphene.Field(
        Promotion, description="Promotion to which the rule belongs."
    )
    channels = PermissionsField(
        NonNullList(Channel),
        description="List of channels where the rule applies.",
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    reward_value_type = RewardValueTypeEnum(
        description="The type of reward value of the promotion rule."
    )
    catalogue_predicate = JSON(
        description=(
            "The catalogue predicate that must be met to apply the rule reward."
        ),
    )
    reward_value = PositiveDecimal(
        description=(
            "The reward value of the promotion rule. Defines the discount value "
            "applied when the rule conditions are met."
        )
    )
    translation = TranslationField(PromotionRuleTranslation, type_name="promotion rule")

    class Meta:
        description = (
            "Represents the promotion rule that specifies the conditions that must "
            "be met to apply the promotion discount." + ADDED_IN_317 + PREVIEW_FEATURE
        )
        interfaces = [relay.Node]
        model = models.PromotionRule
        doc_category = DOC_CATEGORY_DISCOUNTS

    @staticmethod
    def resolve_promotion(root: models.PromotionRule, info: ResolveInfo):
        return PromotionByIdLoader(info.context).load(root.promotion_id)

    @staticmethod
    def resolve_channels(root: models.PromotionRule, info: ResolveInfo):
        return ChannelsByPromotionRuleIdLoader(info.context).load(root.id)


class PromotionCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        node = Promotion
