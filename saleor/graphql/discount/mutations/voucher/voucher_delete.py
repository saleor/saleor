import graphene

from saleor.discount import models

from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelDeleteMutation
from ....core.types import DiscountError
from ....directives import doc, webhook_events
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Voucher


@doc(category=DOC_CATEGORY_DISCOUNTS)
@webhook_events(async_events={WebhookEventAsyncType.VOUCHER_DELETED})
class VoucherDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to delete.")

    class Meta:
        description = "Deletes a voucher."
        model = models.Voucher
        object_type = Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)
        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, code):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.voucher_deleted, instance, code)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        """Perform a mutation that deletes a model instance."""
        instance = cls.get_instance(info, external_reference=external_reference, id=id)

        cls.clean_instance(info, instance)
        db_id = instance.id
        code = instance.codes.first().code
        instance.delete()

        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id

        cls.post_save_action(info, instance, code)
        return cls.success_response(instance)
