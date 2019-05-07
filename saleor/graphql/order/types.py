import graphene
import graphene_django_optimizer as gql_optimizer
from django.core.exceptions import ValidationError
from graphene import relay

from ...order import models
from ...order.models import FulfillmentStatus
from ...product.templatetags.product_images import get_product_image_thumbnail
from ..account.types import User
from ..core.connection import CountableDjangoObjectType
from ..core.types.common import Image
from ..core.types.money import Money, TaxedMoney
from ..payment.types import OrderAction, Payment, PaymentChargeStatusEnum
from ..product.types import ProductVariant
from ..shipping.types import ShippingMethod
from .enums import OrderEventsEmailsEnum, OrderEventsEnum
from .utils import applicable_shipping_methods, validate_draft_order


class OrderEvent(CountableDjangoObjectType):
    date = graphene.types.datetime.DateTime(
        description='Date when event happened at in ISO 8601 format.')
    type = OrderEventsEnum(description='Order event type')
    user = graphene.Field(
        User, id=graphene.Argument(graphene.ID),
        description='User who performed the action.')
    message = graphene.String(
        description='Content of a note added to the order.')
    email = graphene.String(description='Email of the customer')
    email_type = OrderEventsEmailsEnum(
        description='Type of an email sent to the customer')
    amount = graphene.Float(description='Amount of money.')
    quantity = graphene.Int(description='Number of items.')
    composed_id = graphene.String(
        description='Composed id of the Fulfillment.')
    order_number = graphene.String(
        description='User-friendly number of an order.')
    oversold_items = graphene.List(
        graphene.String, description='List of oversold lines names.')

    class Meta:
        description = 'History log of the order.'
        model = models.OrderEvent
        interfaces = [relay.Node]
        only_fields = ['id']

    def resolve_email(self, _info):
        return self.parameters.get('email', None)

    def resolve_email_type(self, _info):
        return self.parameters.get('email_type', None)

    def resolve_amount(self, _info):
        amount = self.parameters.get('amount', None)
        return float(amount) if amount else None

    def resolve_quantity(self, _info):
        quantity = self.parameters.get('quantity', None)
        return int(quantity) if quantity else None

    def resolve_message(self, _info):
        return self.parameters.get('message', None)

    def resolve_composed_id(self, _info):
        return self.parameters.get('composed_id', None)

    def resolve_oversold_items(self, _info):
        return self.parameters.get('oversold_items', None)

    def resolve_order_number(self, _info):
        return self.order_id


class FulfillmentLine(CountableDjangoObjectType):
    order_line = graphene.Field(lambda: OrderLine)

    class Meta:
        description = 'Represents line of the fulfillment.'
        interfaces = [relay.Node]
        model = models.FulfillmentLine
        only_fields = ['id', 'quantity']

    @gql_optimizer.resolver_hints(prefetch_related='order_line')
    def resolve_order_line(self, _info):
        return self.order_line


class Fulfillment(CountableDjangoObjectType):
    lines = gql_optimizer.field(
        graphene.List(
            FulfillmentLine,
            description='List of lines for the fulfillment'),
        model_field='lines')
    status_display = graphene.String(
        description='User-friendly fulfillment status.')

    class Meta:
        description = 'Represents order fulfillment.'
        interfaces = [relay.Node]
        model = models.Fulfillment
        only_fields = [
            'fulfillment_order', 'id', 'shipping_date', 'status',
            'tracking_number']

    def resolve_lines(self, _info):
        return self.lines.all()

    def resolve_status_display(self, _info):
        return self.get_status_display()


class OrderLine(CountableDjangoObjectType):
    thumbnail_url = graphene.String(
        description='The URL of a main thumbnail for the ordered product.',
        size=graphene.Int(description='Size of the image'),
        deprecation_reason=(
            'thumbnailUrl is deprecated, use thumbnail instead'))
    thumbnail = graphene.Field(
        Image, description='The main thumbnail for the ordered product.',
        size=graphene.Argument(graphene.Int, description='Size of thumbnail'))
    unit_price = graphene.Field(
        TaxedMoney, description='Price of the single item in the order line.')
    variant = graphene.Field(
        ProductVariant,
        required=False,
        description='''
            A purchased product variant. Note: this field may be null if the
            variant has been removed from stock at all.''')

    class Meta:
        description = 'Represents order line of particular order.'
        model = models.OrderLine
        interfaces = [relay.Node]
        only_fields = [
            'digital_content_url', 'id', 'is_shipping_required',
            'product_name', 'product_sku', 'quantity', 'quantity_fulfilled',
            'tax_rate', 'translated_product_name']

    @gql_optimizer.resolver_hints(
        prefetch_related=['variant__images', 'variant__product__images'])
    def resolve_thumbnail_url(self, info, size=None):
        if not self.variant_id:
            return None
        if not size:
            size = 255
        url = get_product_image_thumbnail(
            self.variant.get_first_image(), size, method='thumbnail')
        return info.context.build_absolute_uri(url)

    @gql_optimizer.resolver_hints(
        prefetch_related=['variant__images', 'variant__product__images'])
    def resolve_thumbnail(self, info, *, size=None):
        if not self.variant_id:
            return None
        if not size:
            size = 255
        image = self.variant.get_first_image()
        url = get_product_image_thumbnail(image, size, method='thumbnail')
        alt = image.alt if image else None
        return Image(alt=alt, url=info.context.build_absolute_uri(url))

    def resolve_unit_price(self, _info):
        return self.unit_price


class Order(CountableDjangoObjectType):
    fulfillments = gql_optimizer.field(
        graphene.List(
            Fulfillment, required=True,
            description='List of shipments for the order.'),
        model_field='fulfillments')
    lines = gql_optimizer.field(
        graphene.List(
            lambda: OrderLine, required=True,
            description='List of order lines.'),
        model_field='lines')
    actions = graphene.List(
        OrderAction, description='''List of actions that can be performed in
        the current state of an order.''', required=True)
    available_shipping_methods = graphene.List(
        ShippingMethod, required=False,
        description='Shipping methods that can be used with this order.')
    number = graphene.String(description='User-friendly number of an order.')
    is_paid = graphene.Boolean(
        description='Informs if an order is fully paid.')
    payment_status = PaymentChargeStatusEnum(
        description='Internal payment status.')
    payment_status_display = graphene.String(
        description='User-friendly payment status.')
    payments = gql_optimizer.field(
        graphene.List(
            Payment, description='List of payments for the order'),
        model_field='payments')
    total = graphene.Field(
        TaxedMoney, description='Total amount of the order.')
    shipping_price = graphene.Field(
        TaxedMoney, description='Total price of shipping.')
    subtotal = graphene.Field(
        TaxedMoney,
        description='The sum of line prices not including shipping.')
    status_display = graphene.String(description='User-friendly order status.')
    can_finalize = graphene.Boolean(
        description=(
            'Informs whether a draft order can be finalized'
            '(turned into a regular order).'), required=True)
    total_authorized = graphene.Field(
        Money, description='Amount authorized for the order.')
    total_captured = graphene.Field(
        Money, description='Amount captured by payment.')
    events = gql_optimizer.field(
        graphene.List(
            OrderEvent,
            description='List of events associated with the order.'),
        model_field='events')
    total_balance = graphene.Field(
        Money,
        description='''The difference between the paid and the order total
        amount.''', required=True)
    user_email = graphene.String(
        required=False, description='Email address of the customer.')
    is_shipping_required = graphene.Boolean(
        description='Returns True, if order requires shipping.',
        required=True)

    class Meta:
        description = 'Represents an order in the shop.'
        interfaces = [relay.Node]
        model = models.Order
        only_fields = [
            'billing_address', 'created', 'customer_note', 'discount_amount',
            'discount_name', 'display_gross_prices', 'id', 'language_code',
            'shipping_address', 'shipping_method', 'shipping_method_name',
            'shipping_price', 'status', 'token', 'tracking_client_id',
            'translated_discount_name', 'user', 'voucher', 'weight']

    def resolve_shipping_price(self, _info):
        return self.shipping_price

    @gql_optimizer.resolver_hints(prefetch_related='payments__transactions')
    def resolve_actions(self, _info):
        actions = []
        payment = self.get_last_payment()
        if self.can_capture(payment):
            actions.append(OrderAction.CAPTURE)
        if self.can_mark_as_paid():
            actions.append(OrderAction.MARK_AS_PAID)
        if self.can_refund(payment):
            actions.append(OrderAction.REFUND)
        if self.can_void(payment):
            actions.append(OrderAction.VOID)
        return actions

    def resolve_subtotal(self, _info):
        return self.get_subtotal()

    def resolve_total(self, _info):
        return self.total

    @gql_optimizer.resolver_hints(prefetch_related='payments__transactions')
    def resolve_total_authorized(self, _info):
        # FIXME adjust to multiple payments in the future
        return self.total_authorized

    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_total_captured(self, _info):
        # FIXME adjust to multiple payments in the future
        return self.total_captured

    def resolve_total_balance(self, _info):
        return self.total_balance

    def resolve_fulfillments(self, info):
        user = info.context.user
        if user.is_staff:
            qs = self.fulfillments.all()
        else:
            qs = self.fulfillments.exclude(status=FulfillmentStatus.CANCELED)
        return qs.order_by('pk')

    def resolve_lines(self, _info):
        return self.lines.all().order_by('pk')

    def resolve_events(self, _info):
        return self.events.all().order_by('pk')

    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_is_paid(self, _info):
        return self.is_fully_paid()

    def resolve_number(self, _info):
        return str(self.pk)

    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_payment_status(self, _info):
        return self.get_payment_status()

    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_payment_status_display(self, _info):
        return self.get_payment_status_display()

    def resolve_payments(self, _info):
        return self.payments.all()

    def resolve_status_display(self, _info):
        return self.get_status_display()

    @staticmethod
    def resolve_can_finalize(self, _info):
        try:
            validate_draft_order(self)
        except ValidationError:
            return False
        return True

    @gql_optimizer.resolver_hints(select_related='user')
    def resolve_user_email(self, _info):
        if self.user_email:
            return self.user_email
        if self.user_id:
            return self.user.email
        return None

    def resolve_available_shipping_methods(self, _info):
        return applicable_shipping_methods(
            self, self.get_subtotal().gross.amount)

    def resolve_is_shipping_required(self, _info):
        return self.is_shipping_required()
