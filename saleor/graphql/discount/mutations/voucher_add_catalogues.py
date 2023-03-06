import graphene

from ....permission.enums import DiscountPermissions
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.types import DiscountError, NonNullList
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Voucher
from .sale_base_discount_catalogue import BaseDiscountCatalogueMutation


class CatalogueInput(graphene.InputObjectType):
    products = NonNullList(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    categories = NonNullList(
        graphene.ID,
        description="Categories related to the discount.",
        name="categories",
    )
    collections = NonNullList(
        graphene.ID,
        description="Collections related to the discount.",
        name="collections",
    )
    variants = NonNullList(
        graphene.ID,
        description="Product variant related to the discount." + ADDED_IN_31,
        name="variants",
    )


class VoucherBaseCatalogueMutation(BaseDiscountCatalogueMutation):
    voucher = graphene.Field(
        Voucher, description="Voucher of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher.")
        input = CatalogueInput(
            required=True,
            description="Fields required to modify catalogue IDs of voucher.",
        )

    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info: ResolveInfo, **data):
        response = super().mutate(root, info, **data)
        if response.voucher:
            response.voucher = ChannelContext(node=response.voucher, channel_slug=None)
        return response


class VoucherAddCatalogues(VoucherBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        voucher = cls.get_node_or_error(
            info, data.get("id"), only_type=Voucher, field="voucher_id"
        )
        input_data = data.get("input", {})
        cls.add_catalogues_to_node(voucher, input_data)

        if input_data:
            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(manager.voucher_updated, voucher)

        return VoucherAddCatalogues(voucher=voucher)
