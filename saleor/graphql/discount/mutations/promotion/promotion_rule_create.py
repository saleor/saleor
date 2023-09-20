from collections import defaultdict
from typing import DefaultDict, List

import graphene
from django.core.exceptions import ValidationError

from .....discount import RewardValueType, events, models
from .....permission.enums import DiscountPermissions
from .....product.tasks import update_products_discounted_prices_for_promotion_task
from .....webhook.event_types import WebhookEventAsyncType
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_317, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import Error
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PromotionRuleCreateErrorCode
from ...types import PromotionRule
from ...utils import get_products_for_rule
from ...validators import clean_predicate
from ..utils import clear_promotion_old_sale_id
from .promotion_create import PromotionRuleInput
from .validators import clean_fixed_discount_value, clean_percentage_discount_value


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
        description = "Creates a new promotion rule." + ADDED_IN_317 + PREVIEW_FEATURE
        model = models.PromotionRule
        object_type = PromotionRule
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionRuleCreateError
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_RULE_CREATED,
                description="A promotion rule was created.",
            ),
        ]

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
            cls.clean_reward(cleaned_input, errors)

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
    def clean_reward(cls, cleaned_input, errors):
        reward_value = cleaned_input.get("reward_value")
        reward_value_type = cleaned_input.get("reward_value_type")
        if reward_value_type is None:
            errors["reward_value_type"].append(
                ValidationError(
                    "The rewardValueType is required for when "
                    "cataloguePredicate is provided.",
                    code=PromotionRuleCreateErrorCode.REQUIRED.value,
                )
            )
        if reward_value is None:
            errors["reward_value"].append(
                ValidationError(
                    "The rewardValue is required when cataloguePredicate "
                    "is provided.",
                    code=PromotionRuleCreateErrorCode.REQUIRED.value,
                )
            )
        if reward_value and reward_value_type:
            cls.clean_reward_value(
                reward_value, reward_value_type, cleaned_input.get("channels"), errors
            )

    @classmethod
    def clean_reward_value(cls, reward_value, reward_value_type, channels, errors):
        if reward_value_type == RewardValueType.FIXED:
            if not channels:
                errors["channels"].append(
                    ValidationError(
                        "Channels must be specified for FIXED rewardValueType.",
                        code=PromotionRuleCreateErrorCode.REQUIRED.value,
                    )
                )
                return
            currencies = {channel.currency_code for channel in channels}
            if len(currencies) > 1:
                error_code = (
                    PromotionRuleCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.value
                )
                errors["reward_value_type"].append(
                    ValidationError(
                        "For FIXED rewardValueType, all channels must have "
                        "the same currency.",
                        code=error_code,
                    )
                )
                return

            currency = currencies.pop()
            try:
                clean_fixed_discount_value(
                    reward_value,
                    PromotionRuleCreateErrorCode.INVALID_PRECISION.value,
                    currency,
                )
            except ValidationError as error:
                errors["reward_value"].append(error)

        elif reward_value_type == RewardValueType.PERCENTAGE:
            try:
                clean_percentage_discount_value(
                    reward_value, PromotionRuleCreateErrorCode.INVALID.value
                )
            except ValidationError as error:
                errors["reward_value"].append(error)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        products = get_products_for_rule(instance)
        if products:
            update_products_discounted_prices_for_promotion_task.delay(
                list(products.values_list("id", flat=True))
            )
        clear_promotion_old_sale_id(instance.promotion, save=True)
        app = get_app_promise(info.context).get()
        events.rule_created_event(info.context.user, app, [instance])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.promotion_rule_created, instance)
