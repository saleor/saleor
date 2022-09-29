import graphene

from ....core.permissions import DiscountPermissions
from ....discount import models
from ...core.types import DiscountError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Voucher
from .voucher_create import VoucherCreate, VoucherInput


class VoucherUpdate(VoucherCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to update.")
        input = VoucherInput(
            required=True, description="Fields required to update a voucher."
        )

    class Meta:
        description = "Updates a voucher."
        model = models.Voucher
        object_type = Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.voucher_updated, instance)
