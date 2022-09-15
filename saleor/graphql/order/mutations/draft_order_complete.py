import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....account.models import User
from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....core.postgres import FlatConcatSearchVector
from ....core.taxes import zero_taxed_money
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus, models
from ....order.actions import order_created
from ....order.calculations import fetch_order_prices_if_expired
from ....order.error_codes import OrderErrorCode
from ....order.fetch import OrderInfo, OrderLineInfo
from ....order.search import prepare_order_search_vector_value
from ....order.utils import get_order_country
from ....warehouse.management import allocate_preorders, allocate_stocks
from ....warehouse.reservations import is_reservation_enabled
from ...app.dataloaders import load_app
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...site.dataloaders import load_site
from ..types import Order
from ..utils import (
    prepare_insufficient_stock_order_validation_errors,
    validate_draft_order,
)


class DraftOrderComplete(BaseMutation):
    order = graphene.Field(Order, description="Completed order.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the order that will be completed."
        )

    class Meta:
        description = "Completes creating an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def update_user_fields(cls, order):
        if order.user:
            order.user_email = order.user.email
        elif order.user_email:
            try:
                order.user = User.objects.get(email=order.user_email)
            except User.DoesNotExist:
                order.user = None

    @classmethod
    def validate_order(cls, order):
        if not order.is_draft():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "The order is not draft.", code=OrderErrorCode.INVALID.value
                    )
                }
            )

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, id):
        manager = info.context.plugins
        order = cls.get_node_or_error(
            info,
            id,
            only_type=Order,
            qs=models.Order.objects.prefetch_related("lines__variant"),
        )
        order, _ = fetch_order_prices_if_expired(order, manager)
        cls.validate_order(order)

        country = get_order_country(order)
        validate_draft_order(order, country, info.context.plugins)
        cls.update_user_fields(order)
        order.status = OrderStatus.UNFULFILLED

        if not order.is_shipping_required():
            order.shipping_method_name = None
            order.shipping_price = zero_taxed_money(order.currency)
            if order.shipping_address:
                order.shipping_address.delete()
                order.shipping_address = None

        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
        order.save()

        channel = order.channel
        order_lines_info = []
        for line in order.lines.all():
            if line.variant.track_inventory or line.variant.is_preorder_active():
                line_data = OrderLineInfo(
                    line=line, quantity=line.quantity, variant=line.variant
                )
                order_lines_info.append(line_data)
                site = load_site(info.context)
                try:
                    with traced_atomic_transaction():
                        allocate_stocks(
                            [line_data],
                            country,
                            channel,
                            manager,
                            check_reservations=is_reservation_enabled(site.settings),
                        )
                        allocate_preorders(
                            [line_data],
                            channel.slug,
                            check_reservations=is_reservation_enabled(site.settings),
                        )
                except InsufficientStock as exc:
                    errors = prepare_insufficient_stock_order_validation_errors(exc)
                    raise ValidationError({"lines": errors})

        order_info = OrderInfo(
            order=order,
            customer_email=order.get_customer_email(),
            channel=channel,
            payment=order.get_last_payment(),
            lines_data=order_lines_info,
        )
        app = load_app(info.context)
        transaction.on_commit(
            lambda: order_created(
                order_info=order_info,
                user=info.context.user,
                app=app,
                manager=info.context.plugins,
                from_draft=True,
            )
        )
        return DraftOrderComplete(order=order)
