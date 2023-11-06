import graphene

from saleor.discount import models

from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.utils import get_webhooks_for_event
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.mutations import ModelDeleteMutation
from ....core.types import DiscountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Voucher


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
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_DELETED,
                description="A voucher was deleted.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_CODE_DELETED,
                description="A voucher code was deleted.",
            ),
        ]

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)
        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, code_instances):
        manager = get_plugin_manager_promise(info.context).get()
        code_delete_webhook = get_webhooks_for_event(
            WebhookEventAsyncType.VOUCHER_CODE_DELETED
        )
        cls.call_event(manager.voucher_deleted, instance, code_instances[0].code)
        for code in code_instances:
            cls.call_event(
                manager.voucher_code_deleted, code, webhooks=code_delete_webhook
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        """Perform a mutation that deletes a model instance."""
        instance = cls.get_instance(info, external_reference=external_reference, id=id)

        cls.clean_instance(info, instance)
        db_id = instance.id
        code_instances = list(instance.codes.all())
        code_instances_ids = [code_instance.id for code_instance in code_instances]
        instance.delete()

        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        for id, code in zip(code_instances_ids, code_instances):
            code.id = id

        cls.post_save_action(info, instance, code_instances)
        return cls.success_response(instance)
