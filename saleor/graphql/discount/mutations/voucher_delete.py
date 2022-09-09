import graphene

from saleor.discount import models

from ....core.permissions import DiscountPermissions
from ...channel import ChannelContext
from ...core.mutations import ModelDeleteMutation
from ...core.types import DiscountError
from ...plugins.dataloaders import load_plugin_manager
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
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        manager.voucher_deleted(instance)
