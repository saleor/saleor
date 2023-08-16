from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, cast

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

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
    def add_channels(cls, promotion: Promotion, add_channels: List[Dict]):
        rules_data_to_add: List[RuleInfo] = []
        rules_to_update: List[PromotionRule] = []

        rules = promotion.rules.all()
        PromotionRuleChannel = PromotionRule.channels.through
        rule_channel = PromotionRuleChannel.objects.filter(
            Exists(rules.filter(id=OuterRef("promotionrule_id")))
        )
        channelid_ruleid_map = {
            channel_id: rule_id
            for channel_id, rule_id in rule_channel.values_list(
                "channel_id", "promotionrule_id"
            )
        }
        examplary_rule = rules[0]
        for add_channel in add_channels:
            channel = add_channel["channel"]
            discount_value = add_channel["discount_value"]

            if channel.id not in channelid_ruleid_map.keys():
                rules_data_to_add.append(
                    RuleInfo(
                        rule=PromotionRule(
                            promotion=promotion,
                            catalogue_predicate=examplary_rule.catalogue_predicate,
                            reward_value_type=examplary_rule.reward_value_type,
                            reward_value=discount_value,
                        ),
                        channel=channel,
                    )
                )
            else:
                # We ensure that every rule has one or none related channel
                rule_to_update = rules.get(id=channelid_ruleid_map[channel.id])
                rule_to_update.reward_value = discount_value
                rules_to_update.append(rule_to_update)

        old_listing_ids = PromotionRule.get_old_channel_listing_ids(
            len(rules_data_to_add)
        )
        for i in range(len(rules_data_to_add)):
            rules_data_to_add[i].rule.old_channel_listing_id = old_listing_ids[i][0]

        new_rules = [rule_data.rule for rule_data in rules_data_to_add]
        PromotionRule.objects.bulk_create(new_rules)
        rules_channels = [
            PromotionRuleChannel(
                promotionrule=rule_data.rule, channel=rule_data.channel
            )
            for rule_data in rules_data_to_add
        ]
        PromotionRuleChannel.objects.bulk_create(rules_channels)
        PromotionRule.objects.bulk_update(rules_to_update, ["reward_value"])

    @classmethod
    def remove_channels(cls, promotion: Promotion, remove_channels: List[int]):
        rules = promotion.rules.all()
        PromotionRuleChannel = PromotionRule.channels.through
        rule_channel = PromotionRuleChannel.objects.filter(
            channel_id__in=remove_channels
        ).filter(Exists(rules.filter(id=OuterRef("promotionrule_id"))))
        if not rule_channel:
            return
        rules_to_delete_ids = list(
            rule_channel.values_list("promotionrule_id", flat=True)
        )
        # We ensure at least one rule is assigned to promotion in order to
        # determine old sale's type and catalogue
        if len(rule_channel) >= len(rules):
            rule_left_id = rules_to_delete_ids.pop()
            rule_channel.filter(promotionrule_id=rule_left_id).delete()
        rules.filter(id__in=rules_to_delete_ids).delete()

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
    def save(cls, _info: ResolveInfo, promotion: Promotion, cleaned_input: Dict):
        with traced_atomic_transaction():
            cls.add_channels(promotion, cleaned_input.get("add_channels", []))
            cls.remove_channels(promotion, cleaned_input.get("remove_channels", []))
            update_products_discounted_prices_of_promotion_task.delay(promotion.pk)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        object_id = cls.get_global_id_or_error(id, "Sale")
        promotion = Promotion.objects.get(old_sale_id=object_id)
        rule = promotion.rules.first()
        rule = cast(PromotionRule, rule)
        sale_type = rule.reward_value_type

        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)
        cleaned_channels = cls.clean_channels(
            info, input, errors, DiscountErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        cleaned_input = cls.clean_discount_values(
            cleaned_channels, sale_type, errors, DiscountErrorCode.INVALID.value
        )

        if errors:
            raise ValidationError(errors)

        cls.save(info, promotion, cleaned_input)

        # Invalidate dataloader for channel listings
        SaleChannelListingByPromotionIdLoader(info.context).clear(promotion.pk)
        PromotionRulesByPromotionIdLoader(info.context).clear(promotion.pk)

        return SaleChannelListingUpdate(
            sale=ChannelContext(node=promotion, channel_slug=None)
        )
