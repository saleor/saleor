from collections import defaultdict
from copy import deepcopy
from typing import DefaultDict, List

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from .....discount import models
from .....permission.enums import DiscountPermissions
from .....product import models as product_models
from .....product.tasks import update_products_discounted_prices_for_promotion_task
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import Error
from ....discount.utils import get_variants_for_predicate
from ...enums import PromotionRuleCreateErrorCode
from ...types import PromotionRule
from ...validators import clean_predicate
from .promotion_create import PromotionRuleInput


class PromotionRuleCreateInput(PromotionRuleInput):
    promotion = graphene.ID(
        description="The ID of the promotion that rule belongs to.", required=True
    )


class PromotionRuleCreateError(Error):
    code = PromotionRuleCreateErrorCode(description="The error code.", required=True)


class PromotionRuleCreate(ModelMutation):
    class Arguments:
        input = PromotionRuleCreateInput(
            description="Fields required to create a promotion rule.", required=True
        )

    class Meta:
        description = "Creates a new promotion rule." + ADDED_IN_315 + PREVIEW_FEATURE
        model = models.PromotionRule
        object_type = PromotionRule
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionRuleCreateError
        doc_category = DOC_CATEGORY_DISCOUNTS

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.PromotionRule, data: dict, **kwargs
    ):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        errors: DefaultDict[str, List[ValidationError]] = defaultdict(list)

        if "catalogue_predicate" not in cleaned_input:
            errors["catalogue_predicate"].append(
                ValidationError(
                    "The cataloguePredicate field is required.",
                    code=PromotionRuleCreateErrorCode.REQUIRED.value,
                )
            )
        else:
            if "reward_value_type" not in cleaned_input:
                errors["reward_value_type"].append(
                    ValidationError(
                        "The rewardValueType is required for when "
                        "cataloguePredicate is provided.",
                        code=PromotionRuleCreateErrorCode.REQUIRED.value,
                    )
                )
            if "reward_value" not in cleaned_input:
                errors["reward_value"].append(
                    ValidationError(
                        "The rewardValue is required for when cataloguePredicate "
                        "is provided.",
                        code=PromotionRuleCreateErrorCode.REQUIRED.value,
                    )
                )
            try:
                cleaned_input["catalogue_predicate"] = clean_predicate(
                    cleaned_input.get("catalogue_predicate"),
                    PromotionRuleCreateErrorCode,
                )
            except ValidationError as error:
                errors["catalogue_predicate"].append(error)

        if errors:
            raise ValidationError(errors)
        return cleaned_input

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        variants = get_variants_for_predicate(deepcopy(instance.catalogue_predicate))
        products = product_models.Product.objects.filter(
            Exists(variants.filter(product_id=OuterRef("id")))
        )
        update_products_discounted_prices_for_promotion_task.delay(
            list(products.values_list("id", flat=True))
        )
