import graphene
from django.db import transaction

from .....discount import models
from .....graphql.core.mutations import ModelDeleteMutation
from .....permission.enums import DiscountPermissions
from .....product.tasks import update_products_discounted_prices_for_promotion_task
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import Error
from ....discount.utils import get_products_for_promotion
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PromotionDeleteErrorCode
from ...types import Promotion


class PromotionDeleteError(Error):
    code = PromotionDeleteErrorCode(description="The error code.", required=True)


class PromotionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the promotion to remove."
        )

    class Meta:
        description = "Deletes a promotion." + ADDED_IN_315 + PREVIEW_FEATURE
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionDeleteError
        doc_category = DOC_CATEGORY_DISCOUNTS

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id: str
    ):
        instance = cls.get_node_or_error(info, id, only_type=Promotion)
        manager = get_plugin_manager_promise(info.context).get()
        product_ids = list(
            get_products_for_promotion(instance).values_list("id", flat=True)
        )

        with transaction.atomic():
            response = super().perform_mutation(root, info, id=id)
            cls.call_event(manager.promotion_deleted(instance))
            update_products_discounted_prices_for_promotion_task.delay(product_ids)
        return response
