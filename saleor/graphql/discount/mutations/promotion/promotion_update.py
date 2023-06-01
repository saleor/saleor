import graphene
from django.core.exceptions import ValidationError

from .....discount import models
from .....permission.enums import DiscountPermissions
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import Error
from ....core.validators import validate_end_is_after_start
from ...enums import PromotionUpdateErrorCode
from ...types import Promotion
from .promotion_create import PromotionInput


class PromotionUpdateError(Error):
    code = PromotionUpdateErrorCode(description="The error code.", required=True)


class PromotionUpdateInput(PromotionInput):
    name = graphene.String(description="Promotion name.")


class PromotionUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of the promotion to update.")
        input = PromotionUpdateInput(
            description="Fields required to update a promotion.", required=True
        )

    class Meta:
        description = "Updates an existing promotion." + ADDED_IN_315 + PREVIEW_FEATURE
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionUpdateError
        doc_category = DOC_CATEGORY_DISCOUNTS

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.Promotion, data: dict, **kwargs
    ):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        start_date = cleaned_input.get("start_date")
        end_date = cleaned_input.get("end_date")
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = PromotionUpdateErrorCode.INVALID.value
            raise ValidationError({"endDate": error})
        return cleaned_input

    @classmethod
    def send_sale_notifications(cls, manager, instance):
        # TODO: implement the notifications
        pass
