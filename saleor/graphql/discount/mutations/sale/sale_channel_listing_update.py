from collections import defaultdict
from typing import cast

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from .....channel.models import Channel
from .....core.tracing import traced_atomic_transaction
from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, PromotionRule
from .....discount.utils.promotion import mark_catalogue_promotion_rules_as_dirty
from .....permission.enums import DiscountPermissions
from .....product.utils.product import mark_products_in_channels_as_dirty
from ....channel import ChannelContext
from ....channel.mutations import BaseChannelListingMutation
from ....core import ResolveInfo
from ....core.descriptions import DEPRECATED_IN_3X_MUTATION
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.scalars import PositiveDecimal
from ....core.types import BaseInputObjectType, DiscountError, NonNullList
from ....core.utils import raise_validation_error
from ....core.validators import validate_price_precision
from ....discount.types import Sale
from ...dataloaders import (
    PromotionRulesByPromotionIdLoader,
    SaleChannelListingByPromotionIdLoader,
)
from ...utils import get_products_for_rule


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
    def add_channels(
        cls,
        promotion: Promotion,
        exemplary_rule: PromotionRule,
        add_channels: list[dict],
    ):
        channel_id_rule_map = cls.get_channe_id_to_rule_map(promotion)
        rules_to_create: list[tuple[Channel, PromotionRule]] = []
        rules_to_update: list[tuple[Channel, PromotionRule]] = []
        for add_channel in add_channels:
            channel = add_channel["channel"]
            discount_value = add_channel["discount_value"]

            if channel.id not in channel_id_rule_map:
                rules_to_create.append(
                    (
                        channel,
                        PromotionRule(
                            promotion=promotion,
                            catalogue_predicate=exemplary_rule.catalogue_predicate,
                            reward_value_type=exemplary_rule.reward_value_type,
                            reward_value=discount_value,
                        ),
                    )
                )
            else:
                # We ensure that every rule has one or none related channel
                rule = channel_id_rule_map[channel.id]
                rule.reward_value = discount_value
                rules_to_update.append(rule)

        old_listing_ids = PromotionRule.get_old_channel_listing_ids(
            len(rules_to_create)
        )
        for idx, (channel, rule) in enumerate(rules_to_create):
            rule.old_channel_listing_id = old_listing_ids[idx][0]

        cls.save_promotion_rules(rules_to_create, rules_to_update)

    @classmethod
    def save_promotion_rules(cls, rules_to_create, rules_to_update):
        new_rules = [rule_data[1] for rule_data in rules_to_create]
        PromotionRule.objects.bulk_create(new_rules)

        PromotionRuleChannel = PromotionRule.channels.through
        rules_channels = [
            PromotionRuleChannel(promotionrule=rule, channel=channel)
            for channel, rule in rules_to_create
        ]

        PromotionRuleChannel.objects.bulk_create(rules_channels)
        PromotionRule.objects.bulk_update(rules_to_update, ["reward_value"])

    @classmethod
    def get_channe_id_to_rule_map(cls, promotion):
        if not promotion:
            return {}
        rules = promotion.rules.all()
        PromotionRuleChannel = PromotionRule.channels.through
        rule_channel = PromotionRuleChannel.objects.filter(
            Exists(rules.filter(id=OuterRef("promotionrule_id")))
        )
        rules_in_bulk = rules.in_bulk()
        return {
            channel_id: rules_in_bulk[rule_id]
            for channel_id, rule_id in rule_channel.values_list(
                "channel_id", "promotionrule_id"
            )
        }

    @classmethod
    def remove_channels(cls, promotion: Promotion, remove_channels: list[int]):
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
        errors: defaultdict[str, list[ValidationError]],
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
    def save(
        cls,
        _info: ResolveInfo,
        promotion: Promotion,
        rule: PromotionRule,
        cleaned_input: dict,
    ):
        add_channels = cleaned_input.get("add_channels", [])
        remove_channels = cleaned_input.get("remove_channels", [])
        if remove_channels and not add_channels:
            # In case of only removing the channels, we need to mark the product to be
            # recalculated.
            product_ids = list(get_products_for_rule(rule).values_list("id", flat=True))
            mark_as_dirty_func = mark_products_in_channels_as_dirty
            func_arg = {int(channel_id): product_ids for channel_id in remove_channels}
        else:
            mark_as_dirty_func = mark_catalogue_promotion_rules_as_dirty  # type: ignore
            func_arg = [promotion.pk]  # type: ignore[assignment]

        with traced_atomic_transaction():
            cls.add_channels(promotion, rule, cleaned_input.get("add_channels", []))
            cls.remove_channels(promotion, cleaned_input.get("remove_channels", []))
            cls.call_event(mark_as_dirty_func, func_arg)

    @classmethod
    def get_instance(cls, id):
        object_id = cls.get_global_id_or_error(id, "Sale")
        try:
            return Promotion.objects.get(old_sale_id=object_id)
        except Promotion.DoesNotExist:
            raise_validation_error(
                field="id",
                message="Sale with given ID can't be found.",
                code=DiscountErrorCode.NOT_FOUND,
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        promotion = cls.get_instance(id)
        rule = promotion.rules.first()
        rule = cast(PromotionRule, rule)
        sale_type = rule.reward_value_type

        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)
        cleaned_channels = cls.clean_channels(
            info, input, errors, DiscountErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        cleaned_input = cls.clean_discount_values(
            cleaned_channels, sale_type, errors, DiscountErrorCode.INVALID.value
        )

        if errors:
            raise ValidationError(errors)

        cls.save(info, promotion, rule, cleaned_input)

        # Invalidate dataloader for channel listings
        SaleChannelListingByPromotionIdLoader(info.context).clear(promotion.pk)
        PromotionRulesByPromotionIdLoader(info.context).clear(promotion.pk)

        return SaleChannelListingUpdate(
            sale=ChannelContext(node=promotion, channel_slug=None)
        )
