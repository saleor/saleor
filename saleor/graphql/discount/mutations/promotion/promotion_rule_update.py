import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from .....discount import RewardValueType, events, models
from .....discount.utils import get_current_products_for_rules
from .....permission.enums import DiscountPermissions
from .....product.utils.product import mark_products_for_recalculate_discounted_price
from .....webhook.event_types import WebhookEventAsyncType
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_317, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import Error, NonNullList
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ....utils.validators import check_for_duplicates
from ...enums import PromotionRuleUpdateErrorCode
from ...inputs import PromotionRuleBaseInput
from ...types import PromotionRule
from ...utils import get_products_for_rule
from ..utils import clear_promotion_old_sale_id
from .validators import (
    clean_fixed_discount_value,
    clean_percentage_discount_value,
    clean_predicate,
)


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
            "Updates an existing promotion rule." + ADDED_IN_317 + PREVIEW_FEATURE
        )
        model = models.PromotionRule
        object_type = PromotionRule
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionRuleUpdateError
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_RULE_UPDATED,
                description="A promotion rule was updated.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)

        previous_products = get_current_products_for_rules(
            models.PromotionRule.objects.filter(id=instance.id)
        )
        previous_product_ids = set(previous_products.values_list("id", flat=True))
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_actions(info, instance, previous_product_ids)

        return cls.success_response(instance)

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.PromotionRule, data, **kwargs
    ):
        error = check_for_duplicates(
            data, "add_channels", "remove_channels", error_class_field="channels"
        )
        if error:
            error.code = PromotionRuleUpdateErrorCode.DUPLICATED_INPUT_ITEM.value
            raise ValidationError({"addChannels": error, "removeChannels": error})
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        cls.clean_reward(instance, cleaned_input)
        if catalogue_predicate := cleaned_input.get("catalogue_predicate"):
            try:
                cleaned_input["catalogue_predicate"] = clean_predicate(
                    catalogue_predicate, PromotionRuleUpdateErrorCode
                )
            except ValidationError as error:
                raise ValidationError({"catalogue_predicate": error})
        return cleaned_input

    @classmethod
    def clean_reward(cls, instance, cleaned_input):
        """Validate reward value and reward value type.

        - Fixed reward value type requires channels with the same currency code
        to be specified.
        - Validate price precision for fixed reward value.
        - Check if percentage reward value is not above 100.
        """
        channel_currencies = set(
            instance.channels.values_list("currency_code", flat=True)
        )
        if add_channels := cleaned_input.get("add_channels"):
            channel_currencies.update(
                [channel.currency_code for channel in add_channels]
            )
        if remove_channels := cleaned_input.get("remove_channels"):
            channel_currencies = channel_currencies - {
                channel.currency_code for channel in remove_channels
            }

        if "reward_value" in cleaned_input or "reward_value_type" in cleaned_input:
            reward_value = cleaned_input.get("reward_value") or instance.reward_value
            reward_value_type = (
                cleaned_input.get("reward_value_type") or instance.reward_value_type
            )
            if reward_value_type == RewardValueType.FIXED:
                if not channel_currencies:
                    field = (
                        "reward_value_type"
                        if "reward_value_type" in cleaned_input
                        else "remove_channels"
                    )
                    raise ValidationError(
                        {
                            field: ValidationError(
                                "Channels must be specified for FIXED rewardValueType.",
                                code=PromotionRuleUpdateErrorCode.MISSING_CHANNELS.value,
                            )
                        }
                    )
                if len(channel_currencies) > 1:
                    field = (
                        "reward_value_type"
                        if "reward_value_type" in cleaned_input
                        else "add_channels"
                    )
                    error_code = PromotionRuleUpdateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.value
                    raise ValidationError(
                        {
                            field: ValidationError(
                                "Channels must have the same currency code "
                                "for FIXED rewardValueType.",
                                code=error_code,
                            )
                        }
                    )
                currency = channel_currencies.pop()
                try:
                    clean_fixed_discount_value(
                        reward_value,
                        PromotionRuleUpdateErrorCode.INVALID_PRECISION.value,
                        currency,
                    )
                except ValidationError as error:
                    raise ValidationError({"reward_value": error})
            elif reward_value_type == RewardValueType.PERCENTAGE:
                try:
                    clean_percentage_discount_value(
                        reward_value, PromotionRuleUpdateErrorCode.INVALID.value
                    )
                except ValidationError as error:
                    raise ValidationError({"reward_value": error})

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with transaction.atomic():
            super()._save_m2m(info, instance, cleaned_data)
            if remove_channels := cleaned_data.get("remove_channels"):
                instance.channels.remove(*remove_channels)
            if add_channels := cleaned_data.get("add_channels"):
                instance.channels.add(*add_channels)

    @classmethod
    def post_save_actions(cls, info: ResolveInfo, instance, previous_product_ids):
        products = get_products_for_rule(instance, update_rule_variants=True)
        product_ids = set(products.values_list("id", flat=True)) | previous_product_ids
        if product_ids:
            mark_products_for_recalculate_discounted_price(
                list(products.values_list("id", flat=True)),
                list(instance.channels.values_list("id", flat=True)),
            )
        clear_promotion_old_sale_id(instance.promotion, save=True)
        app = get_app_promise(info.context).get()
        events.rule_updated_event(info.context.user, app, [instance])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.promotion_rule_updated, instance)
