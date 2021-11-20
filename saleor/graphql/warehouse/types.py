import graphene
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from ...core.permissions import OrderPermissions, ProductPermissions
from ...warehouse import models
from ...warehouse.reservations import is_reservation_enabled
from ..account.dataloaders import AddressByIdLoader
from ..channel import ChannelContext
from ..core.connection import CountableDjangoObjectType
from ..core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_FIELD
from ..decorators import one_of_permissions_required
from ..meta.types import ObjectWithMetadata
from .enums import WarehouseClickAndCollectOptionEnum


class WarehouseInput(graphene.InputObjectType):
    slug = graphene.String(description="Warehouse slug.")
    email = graphene.String(description="The email address of the warehouse.")


class WarehouseCreateInput(WarehouseInput):
    name = graphene.String(description="Warehouse name.", required=True)
    address = graphene.Field(
        "saleor.graphql.account.types.AddressInput",
        description="Address of the warehouse.",
        required=True,
    )
    shipping_zones = graphene.List(
        graphene.ID, description="Shipping zones supported by the warehouse."
    )


class WarehouseUpdateInput(WarehouseInput):
    name = graphene.String(description="Warehouse name.", required=False)
    address = graphene.Field(
        "saleor.graphql.account.types.AddressInput",
        description="Address of the warehouse.",
        required=False,
    )
    click_and_collect_option = WarehouseClickAndCollectOptionEnum(
        description=f"{ADDED_IN_31} Click and collect options: local, all or disabled",
        required=False,
    )
    is_private = graphene.Boolean(
        description=f"{ADDED_IN_31} Visibility of warehouse stocks", required=False
    )


class Warehouse(CountableDjangoObjectType):
    company_name = graphene.String(
        required=True,
        description="Warehouse company name.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `Address.companyName` instead."
        ),
    )
    click_and_collect_option = WarehouseClickAndCollectOptionEnum(
        description=f"{ADDED_IN_31} Click and collect options: local, all or disabled",
        required=True,
    )

    class Meta:
        description = "Represents warehouse."
        model = models.Warehouse
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        only_fields = [
            "id",
            "name",
            "slug",
            "shipping_zones",
            "address",
            "email",
            "is_private",
        ]

    @staticmethod
    def resolve_shipping_zones(root, *_args, **_kwargs):
        instances = root.shipping_zones.all()
        shipping_zones = [
            ChannelContext(node=shipping_zone, channel_slug=None)
            for shipping_zone in instances
        ]
        return shipping_zones

    @staticmethod
    def resolve_company_name(root, info, *_args, **_kwargs):
        def _resolve_company_name(address):
            return address.company_name

        return (
            AddressByIdLoader(info.context)
            .load(root.address_id)
            .then(_resolve_company_name)
        )


class Stock(CountableDjangoObjectType):
    quantity = graphene.Int(
        required=True,
        description="Quantity of a product in the warehouse's possession, "
        "including the allocated stock that is waiting for shipment.",
    )
    quantity_allocated = graphene.Int(
        required=True, description="Quantity allocated for orders"
    )
    quantity_reserved = graphene.Int(
        required=True, description="Quantity reserved for checkouts"
    )

    class Meta:
        description = "Represents stock."
        model = models.Stock
        interfaces = [graphene.relay.Node]
        only_fields = [
            "warehouse",
            "product_variant",
            "quantity",
            "quantity_allocated",
            "quantity_reserved",
        ]

    @staticmethod
    @one_of_permissions_required(
        [ProductPermissions.MANAGE_PRODUCTS, OrderPermissions.MANAGE_ORDERS]
    )
    def resolve_quantity(root, *_args):
        return root.quantity

    @staticmethod
    @one_of_permissions_required(
        [ProductPermissions.MANAGE_PRODUCTS, OrderPermissions.MANAGE_ORDERS]
    )
    def resolve_quantity_allocated(root, *_args):
        return root.allocations.aggregate(
            quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
        )["quantity_allocated"]

    @staticmethod
    @one_of_permissions_required(
        [ProductPermissions.MANAGE_PRODUCTS, OrderPermissions.MANAGE_ORDERS]
    )
    def resolve_quantity_reserved(root, info, *_args):
        if not is_reservation_enabled(info.context.site.settings):
            return 0

        return root.reservations.aggregate(
            quantity_reserved=Coalesce(
                Sum(
                    "quantity_reserved",
                    filter=Q(reserved_until__gt=timezone.now()),
                ),
                0,
            )
        )["quantity_reserved"]

    @staticmethod
    def resolve_product_variant(root, *_args):
        return ChannelContext(node=root.product_variant, channel_slug=None)


class Allocation(CountableDjangoObjectType):
    quantity = graphene.Int(required=True, description="Quantity allocated for orders.")
    warehouse = graphene.Field(
        Warehouse, required=True, description="The warehouse were items were allocated."
    )

    class Meta:
        description = "Represents allocation."
        model = models.Allocation
        interfaces = [graphene.relay.Node]
        only_fields = ["id"]

    @staticmethod
    @one_of_permissions_required(
        [
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
        ]
    )
    def resolve_warehouse(root, *_args):
        return root.stock.warehouse

    @staticmethod
    @one_of_permissions_required(
        [
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
        ]
    )
    def resolve_quantity(root, *_args):
        return root.quantity_allocated
