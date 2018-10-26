import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay
from payments import PaymentStatus

from ...order import OrderEvents, OrderEventsEmails, models
from ...product.templatetags.product_images import get_thumbnail
from ...shipping import models as shipping_models
from ..account.types import User
from ..core.fields import PrefetchingConnectionField
from ..core.types.common import CountableDjangoObjectType
from ..core.types.money import Money, TaxedMoney
from ..shipping.types import ShippingMethod

OrderEventsEnum = graphene.Enum.from_enum(OrderEvents)
OrderEventsEmailsEnum = graphene.Enum.from_enum(OrderEventsEmails)
PaymentStatusEnum = graphene.Enum(
    'PaymentStatusEnum',
    [(code.upper(), code) for code, name in PaymentStatus.CHOICES])


class OrderStatusFilter(graphene.Enum):
    READY_TO_FULFILL = 'READY_TO_FULFILL'
    READY_TO_CAPTURE = 'READY_TO_CAPTURE'


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
    oversold_items = graphene.List(
        graphene.String, description='List of oversold lines names.')

    class Meta:
        description = 'History log of the order.'
        model = models.OrderEvent
        interfaces = [relay.Node]
        exclude_fields = ['order', 'parameters']

    def resolve_email(self, info):
        return self.parameters.get('email', None)

    def resolve_email_type(self, info):
        return self.parameters.get('email_type', None)

    def resolve_amount(self, info):
        amount = self.parameters.get('amount', None)
        return float(amount) if amount else None

    def resolve_quantity(self, info):
        quantity = self.parameters.get('quantity', None)
        return int(quantity) if quantity else None

    def resolve_message(self, info):
        return self.parameters.get('message', None)

    def resolve_composed_id(self, info):
        return self.parameters.get('composed_id', None)

    def resolve_oversold_items(self, info):
        return self.parameters.get('oversold_items', None)


class Fulfillment(CountableDjangoObjectType):
    lines = gql_optimizer.field(
        PrefetchingConnectionField(lambda: FulfillmentLine),
        model_field='lines')
    status_display = graphene.String(
        description='User-friendly fulfillment status.')

    class Meta:
        description = 'Represents order fulfillment.'
        interfaces = [relay.Node]
        model = models.Fulfillment
        exclude_fields = ['order']

    def resolve_lines(self, info):
        return self.lines.all()

    def resolve_status_display(self, info):
        return self.get_status_display()


class FulfillmentLine(CountableDjangoObjectType):
    order_line = graphene.Field(lambda: OrderLine)

    class Meta:
        description = 'Represents line of the fulfillment.'
        interfaces = [relay.Node]
        model = models.FulfillmentLine
        exclude_fields = ['fulfillment']

    @gql_optimizer.resolver_hints(prefetch_related='order_line')
    def resolve_order_line(self, info):
        return self.order_line


class OrderLine(CountableDjangoObjectType):
    thumbnail_url = graphene.String(
        description='The URL of a main thumbnail for the ordered product.',
        size=graphene.Int(description='Size of the image'))
    unit_price = graphene.Field(
        TaxedMoney, description='Price of the single item in the order line.')

    class Meta:
        description = 'Represents order line of particular order.'
        model = models.OrderLine
        interfaces = [relay.Node]
        exclude_fields = [
            'order', 'unit_price_gross', 'unit_price_net', 'variant']

    @gql_optimizer.resolver_hints(
        prefetch_related=['variant__images', 'variant__product__images'])
    def resolve_thumbnail_url(self, info, size=None):
        if not self.variant_id:
            return None
        if not size:
            size = 255
        return get_thumbnail(
            self.variant.get_first_image(), size, method='thumbnail')

    @staticmethod
    def resolve_unit_price(obj, info):
        return obj.unit_price


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
    is_paid = graphene.Boolean(
        description='Informs if an order is fully paid.')
    number = graphene.String(description='User-friendly number of an order.')
    payment_status = PaymentStatusEnum(description='Internal payment status.')
    payment_status_display = graphene.String(
        description='User-friendly payment status.')
    total = graphene.Field(
        TaxedMoney, description='Total amount of the order.')
    shipping_price = graphene.Field(
        TaxedMoney, description='Total price of shipping.')
    subtotal = graphene.Field(
        TaxedMoney,
        description='The sum of line prices not including shipping.')
    status_display = graphene.String(description='User-friendly order status.')
    total_authorized = graphene.Field(
        Money, description='Amount authorized for the order.')
    total_captured = graphene.Field(
        Money, description='Amount captured by payment.')
    events = gql_optimizer.field(
        graphene.List(
            OrderEvent,
            description='List of events associated with the order.'),
        model_field='events')
    user_email = graphene.String(
        required=False, description='Email address of the customer.')
    available_shipping_methods = graphene.List(
        ShippingMethod, required=False,
        description='Shipping methods that can be used with this order.')

    class Meta:
        description = 'Represents an order in the shop.'
        interfaces = [relay.Node]
        model = models.Order
        exclude_fields = [
            'shipping_price_gross', 'shipping_price_net', 'total_gross',
            'total_net']

    @staticmethod
    def resolve_shipping_price(obj, info):
        return obj.shipping_price

    @staticmethod
    def resolve_subtotal(obj, info):
        return obj.get_subtotal()

    @staticmethod
    def resolve_total(obj, info):
        return obj.total

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_total_authorized(obj, info):
        payment = obj.get_last_payment()
        if payment:
            return payment.get_total().gross

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_total_captured(obj, info):
        payment = obj.get_last_payment()
        if payment:
            return payment.get_captured_price()

    @staticmethod
    def resolve_fulfillments(obj, info):
        return obj.fulfillments.all()

    @staticmethod
    def resolve_lines(obj, info):
        return obj.lines.all()

    @staticmethod
    def resolve_events(obj, info):
        return obj.events.all()

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_is_paid(obj, info):
        return obj.is_fully_paid()

    @staticmethod
    def resolve_number(obj, info):
        return str(obj.pk)

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_payment_status(obj, info):
        return obj.get_last_payment_status()

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related='payments')
    def resolve_payment_status_display(obj, info):
        return obj.get_last_payment_status_display()

    @staticmethod
    def resolve_status_display(obj, info):
        return obj.get_status_display()

    @staticmethod
    def resolve_user_email(obj, info):
        if obj.user_email:
            return obj.user_email
        if obj.user_id:
            return obj.user.email
        return None

    @staticmethod
    def resolve_available_shipping_methods(obj, info):
        if not obj.is_shipping_required():
            return None
        if not obj.shipping_address:
            return None
        qs = shipping_models.ShippingMethod.objects
        qs = qs.applicable_shipping_methods(
            price=obj.get_subtotal().gross.amount, weight=obj.get_total_weight(),
            country_code=obj.shipping_address.country.code)
        return qs
