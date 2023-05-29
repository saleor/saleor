import graphene

from ....discount import models
from ....permission.enums import DiscountPermissions
from ...core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.mutations import ModelMutation
from ...core.scalars import JSON, PositiveDecimal
from ...core.types import BaseInputObjectType, Error, NonNullList
from ..enums import PromotionCreateErrorCode, RewardValueTypeEnum
from ..inputs import CataloguePredicateInput
from ..types import Promotion


class PromotionCreateError(Error):
    code = PromotionCreateErrorCode(description="The error code.", required=True)


class PromotionRuleInput(BaseInputObjectType):
    name = graphene.String(description="Promotion rule name.")
    description = JSON(description="Promotion rule description.", required=False)
    channels = NonNullList(
        graphene.ID,
        description="List of channel ids to which the rule should apply to.",
    )
    catalogue_predicate = CataloguePredicateInput(
        description=(
            "Defines the conditions on the catalogue level that must be met "
            "for the reward to be applied."
        ),
        required=False,
    )
    reward_value_type = RewardValueTypeEnum(
        description=(
            "Defines the promotion rule reward value type. "
            "Must be provided together with reward value."
        ),
        required=False,
    )
    reward_value = PositiveDecimal(
        description=(
            "Defines the discount value. Required when catalogue predicate is provided."
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionCreateInput(BaseInputObjectType):
    name = graphene.String(description="Promotion name.")
    description = JSON(description="Promotion description.", required=False)
    start_date = graphene.types.datetime.DateTime(
        description="The start date of the promotion in ISO 8601 format."
    )
    end_date = graphene.types.datetime.DateTime(
        description="The end date of the promotion in ISO 8601 format."
    )
    rules = NonNullList(PromotionRuleInput, description="List of promotion rules.")

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionCreate(ModelMutation):
    class Arguments:
        input = PromotionCreateInput(
            description="Fields requires to create a promotion.", required=True
        )

    class Meta:
        description = "Creates a new promotion." + ADDED_IN_315 + PREVIEW_FEATURE
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionCreateError
