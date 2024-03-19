from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from .....discount import events, models
from .....permission.enums import DiscountPermissions
from .....product.utils.product import mark_products_in_channels_as_dirty
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
from ..utils import (
    clear_promotion_old_sale_id,
    promotion_rule_should_be_marked_with_dirty_variants,
)
from .promotion_create import PromotionRuleInput
from .validators import clean_promotion_rule


class PromotionRuleCreateInput(PromotionRuleInput):
    promotion = graphene.ID(
        description="The ID of the promotion that rule belongs to.",
        required=True,
    )


class PromotionRuleCreateError(Error):
    code = PromotionRuleCreateErrorCode(description="The error code.", required=True)
    rules_limit = graphene.Int(
        description="Limit of rules with orderPredicate defined."
    )
    rules_limit_exceed_by = graphene.Int(
        description="Number of rules with orderPredicate defined exceeding the limit."
    )
    gifts_limit = graphene.Int(description="Limit of gifts assigned to promotion rule.")
    gifts_limit_exceed_by = graphene.Int(
        description=(
            "Number of gifts defined for this promotion rule exceeding the limit."
        )
    )


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
        promotion_value = data.pop("promotion")
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        promotion = cls.get_node_or_error(
            info, promotion_value, field="promotion", only_type="Promotion"
        )
        cleaned_input["promotion"] = promotion
        promotion_type = promotion.type  # type: ignore[union-attr]

        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)
        clean_promotion_rule(
            cleaned_input,
            promotion_type,
            errors,
            PromotionRuleCreateErrorCode,
        )

        if errors:
            raise ValidationError(errors)
        return cleaned_input

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        products = get_products_for_rule(instance, update_rule_variants=True)
        promotion = cleaned_input["promotion"]
        channel_ids = instance.channels.values_list("id", flat=True)

        if promotion_rule_should_be_marked_with_dirty_variants(
            instance, promotion.type, channel_ids
        ):
            if product_ids := set(products.values_list("id", flat=True)):
                cls.call_event(
                    mark_products_in_channels_as_dirty,
                    {channel_id: product_ids for channel_id in channel_ids},
                )

        clear_promotion_old_sale_id(instance.promotion, save=True)
        app = get_app_promise(info.context).get()
        events.rule_created_event(info.context.user, app, [instance])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.promotion_rule_created, instance)
