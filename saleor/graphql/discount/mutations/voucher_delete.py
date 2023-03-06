import graphene

from saleor.discount import models

from ....permission.enums import DiscountPermissions
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import DiscountError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Voucher


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
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.voucher_deleted, instance)
