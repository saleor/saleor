from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from .....core.tracing import traced_atomic_transaction
from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, PromotionRule, SaleChannelListing
from .....discount.sale_converter import create_promotion_for_new_sale
from .....permission.enums import DiscountPermissions
from .....product.models import VariantChannelListingPromotionRule
from .....product.tasks import update_products_discounted_prices_of_sale_task
from ....channel import ChannelContext
from ....channel.mutations import BaseChannelListingMutation
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.scalars import PositiveDecimal
from ....core.types import BaseInputObjectType, DiscountError, NonNullList
from ....core.validators import validate_price_precision
from ....discount.types import Sale
from ...dataloaders import SaleChannelListingBySaleIdLoader

if TYPE_CHECKING:
    from ....discount.models import Sale as SaleModel


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
        description = "Manage sale's availability in channels."
        doc_category = DOC_CATEGORY_DISCOUNTS
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def add_channels(cls, sale: "SaleModel", promotion, add_channels: List[Dict]):
        channelid_rule_map = cls.get_channel_to_rule_id_map(promotion)
        rules_to_create = []
        rules_to_update = []
        examplary_rule: PromotionRule = promotion.rules.first()

        for add_channel in add_channels:
            channel = add_channel["channel"]
            defaults = {"currency": channel.currency_code}
            channel = add_channel["channel"]
            discount_value = add_channel["discount_value"]
            defaults["discount_value"] = discount_value
            channel_listing, _ = SaleChannelListing.objects.update_or_create(
                sale=sale,
                channel=channel,
                defaults=defaults,
            )
            if channel.id not in channelid_rule_map:
                rules_to_create.append(
                    (
                        channel,
                        PromotionRule(
                            promotion=promotion,
                            catalogue_predicate=examplary_rule.catalogue_predicate,
                            reward_value_type=examplary_rule.reward_value_type,
                            reward_value=discount_value,
                            old_channel_listing_id=channel_listing.id,
                        ),
                    )
                )
            else:
                rule = channelid_rule_map[channel.id]
                rule.reward_value = discount_value
                rules_to_update.append(rule)

        cls.save_promotion_rules(rules_to_create, rules_to_update)

    @classmethod
    def get_channel_to_rule_id_map(cls, promotion):
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
    def remove_channels(
        cls,
        sale: "SaleModel",
        promotion,
        remove_channels: List[int],
    ):
        sale.channel_listings.filter(channel_id__in=remove_channels).delete()
        cls.remove_promotion_rules(promotion, remove_channels)

    @classmethod
    def remove_promotion_rules(cls, promotion, remove_channels: List[int]):
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
            VariantChannelListingPromotionRule.objects.filter(
                promotion_rule_id=rule_left_id
            ).delete()
        rules.filter(id__in=rules_to_delete_ids).delete()

    @classmethod
    def save(cls, info: ResolveInfo, sale: "SaleModel", cleaned_input: Dict):
        with traced_atomic_transaction():
            promotion = Promotion.objects.filter(old_sale_id=sale.pk).first()
            if not promotion:
                promotion = create_promotion_for_new_sale(sale)
            cls.add_channels(sale, promotion, cleaned_input.get("add_channels", []))
            cls.remove_channels(
                sale, promotion, cleaned_input.get("remove_channels", [])
            )
            update_products_discounted_prices_of_sale_task.delay(sale.pk)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        sale = cls.get_node_or_error(info, id, only_type=Sale, field="id")
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)
        cleaned_channels = cls.clean_channels(
            info, input, errors, DiscountErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        cleaned_input = cls.clean_discount_values(
            cleaned_channels, sale.type, errors, DiscountErrorCode.INVALID.value
        )

        if errors:
            raise ValidationError(errors)

        cls.save(info, sale, cleaned_input)

        # Invalidate dataloader for channel listings
        SaleChannelListingBySaleIdLoader(info.context).clear(sale.id)

        return SaleChannelListingUpdate(
            sale=ChannelContext(node=sale, channel_slug=None)
        )
