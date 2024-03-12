import graphene
from django.db.models import Exists, OuterRef

from .....core.tracing import traced_atomic_transaction
from .....discount import models
from .....discount.error_codes import DiscountErrorCode
from .....graphql.core.mutations import ModelDeleteMutation
from .....permission.enums import DiscountPermissions
from .....product.utils.product import mark_products_in_channels_as_dirty
from .....webhook.event_types import WebhookEventAsyncType
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import DEPRECATED_IN_3X_MUTATION
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import DiscountError
from ....core.utils import (
    WebhookEventInfo,
    from_global_id_or_error,
    raise_validation_error,
)
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Sale
from ...utils import (
    convert_migrated_sale_predicate_to_catalogue_info,
    get_products_for_rule,
)


class SaleDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to delete.")

    class Meta:
        description = (
            "Deletes a sale."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `promotionDelete` mutation instead."
        )
        model = models.Promotion
        object_type = Sale
        return_field_name = "sale"
        doc_category = DOC_CATEGORY_DISCOUNTS
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.SALE_DELETED,
                description="A sale was deleted.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id: str
    ):
        promotion = cls.get_promotion_instance(id)
        old_sale_id = promotion.old_sale_id
        promotion_id = promotion.id

        rules = promotion.rules.all()
        rule = rules[0]

        PromotionRuleChannel = rules.model.channels.through
        channel_ids = list(
            PromotionRuleChannel.objects.filter(
                Exists(rules.filter(id=OuterRef("promotionrule_id")))
            ).values_list("channel_id", flat=True)
        )
        previous_catalogue = cls.get_catalogue_info(rule)
        product_ids = cls.get_product_ids(rule)
        with traced_atomic_transaction():
            promotion.delete()
            promotion.old_sale_id = old_sale_id
            promotion.id = promotion_id
            response = cls.success_response(promotion)
            response.sale = ChannelContext(node=promotion, channel_slug=None)

            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(manager.sale_deleted, promotion, previous_catalogue)
            cls.call_event(
                mark_products_in_channels_as_dirty,
                {channel_id: product_ids for channel_id in channel_ids},
            )
        return response

    @classmethod
    def get_promotion_instance(cls, id):
        type, _id = from_global_id_or_error(id, raise_error=False)
        if type == "Promotion":
            raise_validation_error(
                field="id",
                message="Provided ID refers to Promotion model. "
                "Please use 'promotionDelete' mutation instead.",
                code=DiscountErrorCode.INVALID.value,
            )
        object_id = cls.get_global_id_or_error(id, "Sale")
        try:
            return models.Promotion.objects.get(old_sale_id=object_id)
        except models.Promotion.DoesNotExist:
            raise_validation_error(
                field="id",
                message="Sale with given ID can't be found.",
                code=DiscountErrorCode.NOT_FOUND,
            )

    @classmethod
    def get_product_ids(cls, rule: models.PromotionRule):
        products = get_products_for_rule(rule)
        return set(products.values_list("id", flat=True))

    @classmethod
    def get_catalogue_info(cls, rule: models.PromotionRule):
        return convert_migrated_sale_predicate_to_catalogue_info(
            rule.catalogue_predicate
        )
