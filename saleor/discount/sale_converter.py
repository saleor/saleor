from typing import Dict, List

from django.db.models import Exists, OuterRef

from ..graphql.discount.mutations.utils import convert_catalogue_info_to_global_ids
from .models import Promotion, PromotionRule
from .utils import fetch_catalogue_info


def get_promotion_rule_for_sale(sale, sale_channel_listing):
    channel_id = sale_channel_listing.channel_id
    promotion = Promotion.objects.filter(old_sale_id=sale.id).first()
    if not promotion:
        promotion = create_promotion(sale)
        return create_promotion_rule(
            promotion,
            sale,
            sale_channel_listing=sale_channel_listing,
        )
    PromotionChannel = PromotionRule.channels.through
    promotion_channels = PromotionChannel.objects.filter(channel_id=channel_id)
    return PromotionRule.objects.filter(
        Exists(promotion_channels.filter(promotionrule_id=OuterRef("pk"))),
        promotion_id=promotion.id,
    ).first()


def get_or_create_promotion(sale):
    promotion = Promotion.objects.filter(old_sale_id=sale.id).first()
    if promotion:
        return promotion
    return create_promotion_for_new_sale(sale)


def create_promotion_for_new_sale(sale, catalogue_data=None):
    promotion = create_promotion(sale)
    create_promotion_rule(promotion, sale, catalogue_data)
    return promotion


def create_promotion(sale):
    return Promotion.objects.create(
        name=sale.name,
        old_sale_id=sale.id,
        start_date=sale.start_date,
        end_date=sale.end_date,
        created_at=sale.created_at,
        updated_at=sale.updated_at,
        metadata=sale.metadata,
        private_metadata=sale.private_metadata,
        last_notification_scheduled_at=sale.notification_sent_datetime,
    )


def create_promotion_rule(
    promotion,
    sale,
    catalogue_data=None,
    sale_channel_listing=None,
):
    if catalogue_data is None:
        catalogue_data = convert_catalogue_info_to_global_ids(
            fetch_catalogue_info(sale)
        )
    catalogue_predicate = create_catalogue_predicate_from_catalogue_data(catalogue_data)
    rule = PromotionRule.objects.create(
        promotion=promotion,
        catalogue_predicate=catalogue_predicate,
        reward_value_type=sale.type,
        reward_value=sale_channel_listing.discount_value,
        old_channel_listing_id=sale_channel_listing.id,
    )
    rule.channels.add(sale_channel_listing.channel_id)
    return rule


def create_catalogue_predicate_from_catalogue_data(catalogue_data):
    predicate: Dict[str, List] = {"OR": []}
    if ids := catalogue_data.get("collections"):
        predicate["OR"].append({"collectionPredicate": {"ids": list(ids)}})
    if ids := catalogue_data.get("categories"):
        predicate["OR"].append({"categoryPredicate": {"ids": list(ids)}})
    if ids := catalogue_data.get("products"):
        predicate["OR"].append({"productPredicate": {"ids": list(ids)}})
    if ids := catalogue_data.get("variants"):
        predicate["OR"].append({"variantPredicate": {"ids": list(ids)}})
    if not predicate.get("OR"):
        predicate = {}

    return predicate


def create_catalogue_predicate_from_sale(sale):
    catalogue_data = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    return create_catalogue_predicate_from_catalogue_data(catalogue_data)
