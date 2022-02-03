import graphene
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from ...core.permissions import OrderPermissions, ProductPermissions
from ...warehouse import models
from ...warehouse.reservations import is_reservation_enabled
from ..account.dataloaders import AddressByIdLoader
from ..channel import ChannelContext
from ..core.connection import CountableConnection, create_connection_slice
from ..core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_FIELD
from ..core.fields import ConnectionField
from ..core.types import ModelObjectType
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


class Warehouse(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    slug = graphene.String(required=True)
    email = graphene.String(required=True)
    is_private = graphene.Boolean(required=True)
    address = graphene.Field("saleor.graphql.account.types.Address", required=True)
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
    shipping_zones = ConnectionField(
        "saleor.graphql.shipping.types.ShippingZoneCountableConnection",
        required=True,
    )

    class Meta:
        description = "Represents warehouse."
        model = models.Warehouse
        interfaces = [graphene.relay.Node, ObjectWithMetadata]

    @staticmethod
    def resolve_shipping_zones(root, info, *_args, **kwargs):
        from ..shipping.types import ShippingZoneCountableConnection

        instances = root.shipping_zones.all()
        slice = create_connection_slice(
            instances, info, kwargs, ShippingZoneCountableConnection
        )

        edges_with_context = []
        for edge in slice.edges:
            node = edge.node
            edge.node = ChannelContext(node=node, channel_slug=None)
            edges_with_context.append(edge)
        slice.edges = edges_with_context

        return slice

    @staticmethod
    def resolve_address(root, info):
        return AddressByIdLoader(info.context).load(root.address_id)

    @staticmethod
    def resolve_company_name(root, info, *_args, **_kwargs):
        def _resolve_company_name(address):
            return address.company_name

        return (
            AddressByIdLoader(info.context)
            .load(root.address_id)
            .then(_resolve_company_name)
        )


class WarehouseCountableConnection(CountableConnection):
    class Meta:
        node = Warehouse


class Stock(ModelObjectType):
    id = graphene.GlobalID(required=True)
    warehouse = graphene.Field(Warehouse, required=True)
    product_variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant", required=True
    )
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


class StockCountableConnection(CountableConnection):
    class Meta:
        node = Stock


class Allocation(graphene.ObjectType):
    id = graphene.GlobalID(required=True)
    quantity = graphene.Int(required=True, description="Quantity allocated for orders.")
    warehouse = graphene.Field(
        Warehouse, required=True, description="The warehouse were items were allocated."
    )

    class Meta:
        description = "Represents allocation."
        model = models.Allocation
        interfaces = [graphene.relay.Node]

    @staticmethod
    def get_node(info, id):
        try:
            return models.Allocation.objects.get(pk=id)
        except models.Allocation.DoesNotExist:
            return None

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
