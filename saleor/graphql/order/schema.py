from typing import Optional

import graphene
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ...core.exceptions import PermissionDenied
from ...order import models
from ...permission.enums import OrderPermissions
from ...permission.utils import has_one_of_permissions
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.context import get_database_connection_name
from ..core.descriptions import ADDED_IN_310, DEPRECATED_IN_3X_FIELD
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.enums import ReportingPeriod
from ..core.fields import (
    BaseField,
    ConnectionField,
    FilterConnectionField,
    PermissionsField,
)
from ..core.scalars import UUID
from ..core.types import FilterInputObjectType, TaxedMoney
from ..core.utils import ext_ref_to_global_id_or_error, from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from ..utils import get_user_or_app_from_context
from .bulk_mutations.draft_orders import DraftOrderBulkDelete, DraftOrderLinesBulkDelete
from .bulk_mutations.order_bulk_cancel import OrderBulkCancel
from .bulk_mutations.order_bulk_create import OrderBulkCreate
from .filters import DraftOrderFilter, OrderFilter
from .mutations.draft_order_complete import DraftOrderComplete
from .mutations.draft_order_create import DraftOrderCreate
from .mutations.draft_order_delete import DraftOrderDelete
from .mutations.draft_order_update import DraftOrderUpdate
from .mutations.fulfillment_approve import FulfillmentApprove
from .mutations.fulfillment_cancel import FulfillmentCancel
from .mutations.fulfillment_refund_products import FulfillmentRefundProducts
from .mutations.fulfillment_return_products import FulfillmentReturnProducts
from .mutations.fulfillment_update_tracking import FulfillmentUpdateTracking
from .mutations.order_cancel import OrderCancel
from .mutations.order_capture import OrderCapture
from .mutations.order_confirm import OrderConfirm
from .mutations.order_discount_add import OrderDiscountAdd
from .mutations.order_discount_delete import OrderDiscountDelete
from .mutations.order_discount_update import OrderDiscountUpdate
from .mutations.order_fulfill import OrderFulfill
from .mutations.order_grant_refund_create import OrderGrantRefundCreate
from .mutations.order_grant_refund_update import OrderGrantRefundUpdate
from .mutations.order_line_delete import OrderLineDelete
from .mutations.order_line_discount_remove import OrderLineDiscountRemove
from .mutations.order_line_discount_update import OrderLineDiscountUpdate
from .mutations.order_line_update import OrderLineUpdate
from .mutations.order_lines_create import OrderLinesCreate
from .mutations.order_mark_as_paid import OrderMarkAsPaid
from .mutations.order_note_add import OrderAddNote, OrderNoteAdd
from .mutations.order_note_update import OrderNoteUpdate
from .mutations.order_refund import OrderRefund
from .mutations.order_update import OrderUpdate
from .mutations.order_update_shipping import OrderUpdateShipping
from .mutations.order_void import OrderVoid
from .resolvers import (
    resolve_draft_orders,
    resolve_homepage_events,
    resolve_order,
    resolve_order_by_token,
    resolve_orders,
    resolve_orders_total,
)
from .sorters import OrderSortField, OrderSortingInput
from .types import Order, OrderCountableConnection, OrderEventCountableConnection


def search_string_in_kwargs(kwargs: dict) -> bool:
    filter_search = kwargs.get("filter", {}).get("search", "") or ""
    return bool(filter_search.strip())


def sort_field_from_kwargs(kwargs: dict) -> Optional[list[str]]:
    return kwargs.get("sort_by", {}).get("field") or None


class OrderFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        filterset_class = OrderFilter


class OrderDraftFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        filterset_class = DraftOrderFilter


class OrderQueries(graphene.ObjectType):
    homepage_events = ConnectionField(
        OrderEventCountableConnection,
        description=(
            "List of activity events to display on "
            "homepage (at the moment it only contains order-events)."
        ),
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
        deprecation_reason=DEPRECATED_IN_3X_FIELD,
    )
    order = BaseField(
        Order,
        description="Look up an order by ID or external reference.",
        id=graphene.Argument(graphene.ID, description="ID of an order."),
        external_reference=graphene.Argument(
            graphene.String,
            description=(
                f"External ID of an order. {ADDED_IN_310}."
                "\n\nRequires one of the following permissions: MANAGE_ORDERS."
            ),
        ),
        doc_category=DOC_CATEGORY_ORDERS,
    )
    orders = FilterConnectionField(
        OrderCountableConnection,
        sort_by=OrderSortingInput(description="Sort orders."),
        filter=OrderFilterInput(description="Filtering options for orders."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of orders.",
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
        doc_category=DOC_CATEGORY_ORDERS,
    )
    draft_orders = FilterConnectionField(
        OrderCountableConnection,
        sort_by=OrderSortingInput(description="Sort draft orders."),
        filter=OrderDraftFilterInput(description="Filtering options for draft orders."),
        description="List of draft orders.",
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
        doc_category=DOC_CATEGORY_ORDERS,
    )
    orders_total = PermissionsField(
        TaxedMoney,
        description="Return the total sales amount from a specific period.",
        period=graphene.Argument(ReportingPeriod, description="A period of time."),
        channel=graphene.Argument(
            graphene.String,
            description="Slug of a channel for which the data should be returned.",
        ),
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
        doc_category=DOC_CATEGORY_ORDERS,
        deprecation_reason=DEPRECATED_IN_3X_FIELD,
    )
    order_by_token = BaseField(
        Order,
        description="Look up an order by token.",
        deprecation_reason=DEPRECATED_IN_3X_FIELD,
        token=graphene.Argument(UUID, description="The order's token.", required=True),
        doc_category=DOC_CATEGORY_ORDERS,
    )

    @staticmethod
    def resolve_homepage_events(_root, info: ResolveInfo, **kwargs):
        qs = resolve_homepage_events(info)
        return create_connection_slice(qs, info, kwargs, OrderEventCountableConnection)

    @staticmethod
    def resolve_order(_root, info: ResolveInfo, *, external_reference=None, id=None):
        validate_one_of_args_is_in_query(
            "id", id, "external_reference", external_reference
        )
        database_connection_name = get_database_connection_name(info.context)
        if not id:
            requester = get_user_or_app_from_context(info.context)
            permissions = [OrderPermissions.MANAGE_ORDERS]
            if not has_one_of_permissions(requester, permissions):
                raise PermissionDenied(permissions=permissions)
            try:
                id = ext_ref_to_global_id_or_error(
                    models.Order, external_reference, database_connection_name
                )
            except ValidationError:
                return None
        _, id = from_global_id_or_error(id, Order)
        return resolve_order(info, id)

    @staticmethod
    def resolve_orders(_root, info: ResolveInfo, *, channel=None, **kwargs):
        if sort_field_from_kwargs(kwargs) == OrderSortField.RANK:
            # sort by RANK can be used only with search filter
            if not search_string_in_kwargs(kwargs):
                raise GraphQLError(
                    "Sorting by RANK is available only when using a search filter."
                )
        if search_string_in_kwargs(kwargs) and not sort_field_from_kwargs(kwargs):
            # default to sorting by RANK if search is used
            # and no explicit sorting is requested
            product_type = info.schema.get_type("OrderSortingInput")
            kwargs["sort_by"] = product_type.create_container(
                {"direction": "-", "field": ["search_rank", "id"]}
            )
        qs = resolve_orders(info, channel)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, OrderCountableConnection)

    @staticmethod
    def resolve_draft_orders(_root, info: ResolveInfo, **kwargs):
        if sort_field_from_kwargs(kwargs) == OrderSortField.RANK:
            # sort by RANK can be used only with search filter
            if not search_string_in_kwargs(kwargs):
                raise GraphQLError(
                    "Sorting by RANK is available only when using a search filter."
                )
        if search_string_in_kwargs(kwargs) and not sort_field_from_kwargs(kwargs):
            # default to sorting by RANK if search is used
            # and no explicit sorting is requested
            product_type = info.schema.get_type("OrderSortingInput")
            kwargs["sort_by"] = product_type.create_container(
                {"direction": "-", "field": ["search_rank", "id"]}
            )
        qs = resolve_draft_orders(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, OrderCountableConnection)

    @staticmethod
    def resolve_orders_total(_root, info: ResolveInfo, *, period, channel=None):
        return resolve_orders_total(info, period, channel)

    @staticmethod
    def resolve_order_by_token(_root, info: ResolveInfo, *, token):
        return resolve_order_by_token(info, token)


class OrderMutations(graphene.ObjectType):
    draft_order_complete = DraftOrderComplete.Field()
    draft_order_create = DraftOrderCreate.Field()
    draft_order_delete = DraftOrderDelete.Field()
    draft_order_bulk_delete = DraftOrderBulkDelete.Field()
    draft_order_lines_bulk_delete = DraftOrderLinesBulkDelete.Field(
        deprecation_reason=DEPRECATED_IN_3X_FIELD
    )
    draft_order_update = DraftOrderUpdate.Field()

    order_add_note = OrderAddNote.Field(
        deprecation_reason=(f"{DEPRECATED_IN_3X_FIELD} Use `orderNoteAdd` instead.")
    )
    order_cancel = OrderCancel.Field()
    order_capture = OrderCapture.Field()
    order_confirm = OrderConfirm.Field()

    order_fulfill = OrderFulfill.Field()
    order_fulfillment_cancel = FulfillmentCancel.Field()
    order_fulfillment_approve = FulfillmentApprove.Field()
    order_fulfillment_update_tracking = FulfillmentUpdateTracking.Field()
    order_fulfillment_refund_products = FulfillmentRefundProducts.Field()
    order_fulfillment_return_products = FulfillmentReturnProducts.Field()

    order_grant_refund_create = OrderGrantRefundCreate.Field()
    order_grant_refund_update = OrderGrantRefundUpdate.Field()

    order_lines_create = OrderLinesCreate.Field()
    order_line_delete = OrderLineDelete.Field()
    order_line_update = OrderLineUpdate.Field()

    order_discount_add = OrderDiscountAdd.Field()
    order_discount_update = OrderDiscountUpdate.Field()
    order_discount_delete = OrderDiscountDelete.Field()

    order_line_discount_update = OrderLineDiscountUpdate.Field()
    order_line_discount_remove = OrderLineDiscountRemove.Field()

    order_note_add = OrderNoteAdd.Field()
    order_note_update = OrderNoteUpdate.Field()

    order_mark_as_paid = OrderMarkAsPaid.Field()
    order_refund = OrderRefund.Field()
    order_update = OrderUpdate.Field()
    order_update_shipping = OrderUpdateShipping.Field()
    order_void = OrderVoid.Field()
    order_bulk_cancel = OrderBulkCancel.Field()
    order_bulk_create = OrderBulkCreate.Field()
