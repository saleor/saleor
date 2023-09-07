from typing import Dict, List

from ..graphql.discount.mutations.utils import convert_catalogue_info_to_global_ids
from .models import Promotion, PromotionRule
from .utils import fetch_catalogue_info


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
    discount_value=None,
    old_channel_listing_id=None,
):
    if catalogue_data is None:
        catalogue_data = convert_catalogue_info_to_global_ids(
            fetch_catalogue_info(sale)
        )
    catalogue_predicate = create_catalogue_predicate_from_catalogue_data(catalogue_data)
    return PromotionRule.objects.create(
        promotion=promotion,
        catalogue_predicate=catalogue_predicate,
        reward_value_type=sale.type,
        reward_value=discount_value,
        old_channel_listing_id=old_channel_listing_id,
    )


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
