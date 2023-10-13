import graphene

from .....discount import events, models
from .....graphql.core.mutations import ModelDeleteMutation
from .....permission.enums import DiscountPermissions
from .....product.tasks import update_products_discounted_prices_for_promotion_task
from .....webhook.event_types import WebhookEventAsyncType
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_317, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import Error
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PromotionRuleDeleteErrorCode
from ...types import PromotionRule
from ...utils import get_products_for_rule
from ..utils import clear_promotion_old_sale_id


class PromotionRuleDeleteError(Error):
    code = PromotionRuleDeleteErrorCode(description="The error code.", required=True)


class PromotionRuleDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the promotion to remove."
        )

    class Meta:
        description = "Deletes a promotion rule." + ADDED_IN_317 + PREVIEW_FEATURE
        model = models.PromotionRule
        object_type = PromotionRule
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionRuleDeleteError
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_RULE_DELETED,
                description="A promotion rule was deleted.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        """Perform a mutation that deletes a model instance."""
        instance = cls.get_instance(info, external_reference=external_reference, id=id)
        cls.clean_instance(info, instance)

        products = get_products_for_rule(instance)
        product_ids = list(products.values_list("id", flat=True))

        db_id = instance.id
        promotion = instance.promotion
        instance.delete()

        clear_promotion_old_sale_id(promotion, save=True)

        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id

        if product_ids:
            update_products_discounted_prices_for_promotion_task.delay(product_ids)

        app = get_app_promise(info.context).get()
        events.rule_deleted_event(info.context.user, app, [instance])

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.promotion_rule_deleted, instance)

        return cls.success_response(instance)
