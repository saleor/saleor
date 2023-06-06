import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from .....discount import models
from .....permission.enums import DiscountPermissions
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import Error, NonNullList
from ....utils.validators import check_for_duplicates
from ...enums import PromotionRuleUpdateErrorCode
from ...inputs import PromotionRuleBaseInput
from ...types import PromotionRule
from ...validators import clean_predicate


class PromotionRuleUpdateError(Error):
    code = PromotionRuleUpdateErrorCode(description="The error code.", required=True)
    channels = NonNullList(
        graphene.ID,
        description="List of channel IDs which causes the error.",
        required=False,
    )


class PromotionRuleUpdateInput(PromotionRuleBaseInput):
    add_channels = NonNullList(
        graphene.ID,
        description="List of channel ids to remove.",
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channel ids to remove.",
    )


class PromotionRuleUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            description="ID of the promotion rule to update.", required=True
        )
        input = PromotionRuleUpdateInput(
            description="Fields required to create a promotion rule.", required=True
        )

    class Meta:
        description = (
            "Updates an existing promotion rule." + ADDED_IN_315 + PREVIEW_FEATURE
        )
        model = models.PromotionRule
        object_type = PromotionRule
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionRuleUpdateError
        doc_category = DOC_CATEGORY_DISCOUNTS

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.PromotionRule, data: dict, **kwargs
    ):
        error = check_for_duplicates(
            data, "add_channels", "remove_channels", error_class_field="channels"
        )
        if error:
            error.code = PromotionRuleUpdateErrorCode.DUPLICATED_INPUT_ITEM.value
            raise ValidationError({"addChannels": error, "removeChannels": error})
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        if catalogue_predicate := cleaned_input.get("catalogue_predicate"):
            try:
                cleaned_input["catalogue_predicate"] = clean_predicate(
                    catalogue_predicate, PromotionRuleUpdateErrorCode
                )
            except ValidationError as error:
                raise ValidationError({"catalogue_predicate": error})
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with transaction.atomic():
            super()._save_m2m(info, instance, cleaned_data)
            if remove_channels := cleaned_data.get("remove_channels"):
                instance.channels.remove(*remove_channels)
            if add_channels := cleaned_data.get("add_channels"):
                instance.channels.add(*add_channels)
