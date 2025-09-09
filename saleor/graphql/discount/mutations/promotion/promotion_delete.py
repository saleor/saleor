import graphene
from django.db import transaction

from .....discount import models
from .....graphql.core.mutations import ModelDeleteMutation
from .....permission.enums import DiscountPermissions
from .....product.utils.product import (
    get_channel_to_products_map_from_rules,
    mark_products_in_channels_as_dirty,
)
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import Error
from ....directives import doc, webhook_events
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PromotionDeleteErrorCode
from ...types import Promotion


@doc(category=DOC_CATEGORY_DISCOUNTS)
class PromotionDeleteError(Error):
    code = PromotionDeleteErrorCode(description="The error code.", required=True)


@doc(category=DOC_CATEGORY_DISCOUNTS)
@webhook_events(async_events={WebhookEventAsyncType.PROMOTION_DELETED})
class PromotionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the promotion to remove."
        )

    class Meta:
        description = "Deletes a promotion."
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionDeleteError

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id: str
    ):
        instance = cls.get_node_or_error(info, id, only_type=Promotion)
        manager = get_plugin_manager_promise(info.context).get()
        rules = instance.rules.all()
        channel_to_products_map = get_channel_to_products_map_from_rules(rules)

        promotion_id = instance.id

        with transaction.atomic():
            response = super().perform_mutation(root, info, id=id)
            instance.id = promotion_id
            cls.call_event(manager.promotion_deleted, instance)
        if channel_to_products_map:
            cls.call_event(mark_products_in_channels_as_dirty, channel_to_products_map)
        return response
