import graphene

from ....discount import models
from ....permission.enums import DiscountPermissions
from ...core import ResolveInfo
from ...core.types import DiscountError
from ...plugins.dataloaders import get_plugin_manager_promise
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
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.voucher_updated, instance)
