from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List
from uuid import UUID

import graphene
from django.core.exceptions import ValidationError

from .....channel.models import Channel
from .....core.tracing import traced_atomic_transaction
from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, PromotionRule
from .....permission.enums import DiscountPermissions
from .....product.tasks import update_products_discounted_prices_of_promotion_task
from ....channel import ChannelContext
from ....channel.mutations import BaseChannelListingMutation
from ....core import ResolveInfo
from ....core.descriptions import DEPRECATED_IN_3X_MUTATION
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.scalars import PositiveDecimal
from ....core.types import BaseInputObjectType, DiscountError, NonNullList
from ....core.validators import validate_price_precision
from ....discount.types import Sale
from ...dataloaders import (
    PromotionRulesByPromotionIdLoader,
    SaleChannelListingByPromotionIdLoader,
)


@dataclass
class RuleInfo:
    rule: PromotionRule
    channel: Channel


@dataclass
class Data:
    promotion: Promotion
    rules: Dict[UUID, PromotionRule]
    channel_rule: Dict[int, PromotionRule]

    @property
    def all_rules(self):
        return [rule for rule in self.rules.values()]

    @property
    def all_channel_ids(self):
        return [channel_id for channel_id in self.channel_rule.keys()]


class SaleChannelListingAddInput(BaseInputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    discount_value = PositiveDecimal(
        required=True, description="The value of the discount."
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class SaleChannelListingInput(BaseInputObjectType):
    add_channels = NonNullList(
        SaleChannelListingAddInput,
        description="List of channels to which the sale should be assigned.",
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels from which the sale should be unassigned.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class SaleChannelListingUpdate(BaseChannelListingMutation):
    sale = graphene.Field(Sale, description="An updated sale instance.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleChannelListingInput(
            required=True,
            description="Fields required to update sale channel listings.",
        )

    class Meta:
        description = (
            "Manage sale's availability in channels."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `promotionRuleCreate` or `promotionRuleUpdate` mutations instead."
        )
        doc_category = DOC_CATEGORY_DISCOUNTS
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def add_channels(cls, data: Data, add_channels: List[Dict]):
        rules_data_to_add: List[RuleInfo] = []
        rules_to_update: List[PromotionRule] = []

        current_channel_ids = data.all_channel_ids
        examplary_rule = data.all_rules[0]
        for add_channel in add_channels:
            channel = add_channel["channel"]
            discount_value = add_channel["discount_value"]

            if channel.id not in current_channel_ids:
                rules_data_to_add.append(
                    RuleInfo(
                        rule=PromotionRule(
                            name=examplary_rule.name,
                            promotion=data.promotion,
                            catalogue_predicate=examplary_rule.catalogue_predicate,
                            reward_value_type=examplary_rule.reward_value_type,
                            reward_value=discount_value,
                        ),
                        channel=channel,
                    )
                )
            else:
                # We ensure that every rule has one or none related channel
                rule_to_update = data.channel_rule[channel.id]
                rule_to_update.reward_value = discount_value
                rules_to_update.append(rule_to_update)

        if rules_data_to_add:
            for rule_data_to_add in rules_data_to_add:
                rule_data_to_add.rule.assign_old_channel_listing_id()

            new_rules = [rule_data.rule for rule_data in rules_data_to_add]

            PromotionRule.objects.bulk_create(new_rules)
            for new_rule in new_rules:
                data.rules.update({new_rule.id: new_rule})

            PromotionRuleChannel = PromotionRule.channels.through
            rules_channels = [
                PromotionRuleChannel(
                    promotionrule=rule_data_to_add.rule,
                    channel=rule_data_to_add.channel,
                )
                for rule_data_to_add in rules_data_to_add
            ]
            PromotionRuleChannel.objects.bulk_create(rules_channels)
            for rule_channel in rules_channels:
                data.channel_rule.update(
                    {rule_channel.channel_id: rule_channel.promotionrule_id}  # type: ignore[attr-defined] # noqa: E501
                )

        if rules_to_update:
            PromotionRule.objects.bulk_update(rules_to_update, ["reward_value"])
            for rule_to_update in rules_to_update:
                data.rules.update({rule_to_update.id: rule_to_update})

    @classmethod
    def remove_channels(cls, data: Data, remove_channels: List[str]):
        rules_to_delete_ids = [
            data.channel_rule[int(channel_id)].id for channel_id in remove_channels
        ]
        # We ensure at least one rule is assigned to promotion in order to
        # determine old sale's type and catalogue
        if len(rules_to_delete_ids) >= len(data.rules):
            rule_left_id = rules_to_delete_ids.pop()
            PromotionRule.channels.through.objects.filter(
                promotionrule_id=rule_left_id
            ).delete()
        PromotionRule.objects.filter(id__in=rules_to_delete_ids).delete()

    @classmethod
    def clean_discount_values(
        cls,
        cleaned_channels,
        sale_type,
        errors: defaultdict[str, List[ValidationError]],
        error_code,
    ):
        channels_with_invalid_value_precision = []
        channels_with_invalid_percentage_value = []
        for cleaned_channel in cleaned_channels.get("add_channels", []):
            channel = cleaned_channel["channel"]
            currency_code = channel.currency_code
            discount_value = cleaned_channel.get("discount_value")
            if not discount_value:
                continue
            if sale_type == DiscountValueType.FIXED:
                try:
                    validate_price_precision(discount_value, currency_code)
                except ValidationError:
                    channels_with_invalid_value_precision.append(
                        cleaned_channel["channel_id"]
                    )
            elif sale_type == DiscountValueType.PERCENTAGE:
                if discount_value > 100:
                    channels_with_invalid_percentage_value.append(
                        cleaned_channel["channel_id"]
                    )

        if channels_with_invalid_value_precision:
            errors["input"].append(
                ValidationError(
                    "Invalid amount precision.",
                    code=error_code,
                    params={"channels": channels_with_invalid_value_precision},
                )
            )
        if channels_with_invalid_percentage_value:
            errors["input"].append(
                ValidationError(
                    "Invalid percentage value.",
                    code=error_code,
                    params={"channels": channels_with_invalid_percentage_value},
                )
            )
        return cleaned_channels

    @classmethod
    def save(cls, _info: ResolveInfo, data: Data, cleaned_input: Dict):
        with traced_atomic_transaction():
            cls.add_channels(data, cleaned_input.get("add_channels", []))
            cls.remove_channels(data, cleaned_input.get("remove_channels", []))
            update_products_discounted_prices_of_promotion_task.delay(data.promotion.pk)

    @classmethod
    def get_initial_data(cls, rules) -> Data:
        promotion = rules[0].promotion
        PromotionRuleChannel = PromotionRule.channels.through
        rule_ids = [rule.id for rule in rules]
        rules_channels = PromotionRuleChannel.objects.filter(
            promotionrule_id__in=rule_ids
        )
        ruleid_rule_map = {rule.pk: rule for rule in rules}
        channelid_rule_map = {
            item.channel_id: ruleid_rule_map[item.promotionrule_id]  # type: ignore[attr-defined] # noqa: E501
            for item in rules_channels
        }
        return Data(promotion, ruleid_rule_map, channelid_rule_map)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        object_id = cls.get_global_id_or_error(id, "Sale")
        promotion = Promotion.objects.get(old_sale_id=object_id)
        rules = promotion.rules.all()
        sale_type = rules[0].reward_value_type

        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)
        cleaned_channels = cls.clean_channels(
            info, input, errors, DiscountErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        cleaned_input = cls.clean_discount_values(
            cleaned_channels, sale_type, errors, DiscountErrorCode.INVALID.value
        )

        if errors:
            raise ValidationError(errors)

        data = cls.get_initial_data(rules)
        cls.save(info, data, cleaned_input)

        # Invalidate dataloader for channel listings
        SaleChannelListingByPromotionIdLoader(info.context).clear(promotion.pk)
        PromotionRulesByPromotionIdLoader(info.context).clear(promotion.pk)

        return SaleChannelListingUpdate(
            sale=ChannelContext(node=promotion, channel_slug=None)
        )
