import graphene
from graphql_jwt.decorators import permission_required

from ...payment import PaymentError
from ...payment.utils import create_payment_method, gateway_authorize, gateway_charge
from ..account.types import AddressInput
from ..checkout.types import Checkout
from ..core.mutations import BaseMutation
from ..core.types.common import Decimal
from .types import PaymentGatewayEnum, PaymentMethod


class PaymentMethodInput(graphene.InputObjectType):
    gateway = PaymentGatewayEnum()
    checkout_id = graphene.ID(description='Checkout ID')
    transaction_token = graphene.Argument(
        graphene.String,
        required=True,
        description='One time transaction token')
    amount = graphene.Argument(
        Decimal, required=True, description='Transaction amount')
    billing_address = AddressInput(description='Billing address')
    store_payment_method = graphene.Argument(
        graphene.Boolean,
        default_value=False,
        description='Store card for further usage')


class CheckoutPaymentMethodCreate(BaseMutation):
    class Arguments:
        input = PaymentMethodInput(
            required=True, description='Payment method details')

    transaction_id = graphene.String()
    transaction_success = graphene.String()

    class Meta:
        description = 'Creates credit card transaction.'

    @classmethod
    def mutate(cls, root, info, input):
        # FIXME: improve error handling
        errors = []
        checkout = cls.get_node_or_error(
            info, input['checkout_id'], errors, 'checkout_id',
            only_type=Checkout)
        if not checkout:
            return CheckoutPaymentMethodCreate(errors=errors)

        billing_data = {}
        extra_data = cls.get_extra_info(info)
        if input['billing_address']:
            billing_data = cls.clean_billing_address(input['billing_address'])

        # create payment method
        payment_method = create_payment_method(
            variant=input['gateway'],
            billing_email=checkout.email,
            extra_data=extra_data,
            total=input['amount'],
            checkout=checkout,
            **billing_data)
        # authorize payment
        try:
            transaction = gateway_authorize(payment_method, input['transaction_token'])
        except PaymentError as exc:
            msg = str(exc)
            cls.add_error(field='transaction_token', message=msg, errors=errors)

        return CheckoutPaymentMethodCreate(
            transaction_id=transaction.token,
            transaction_success=transaction.is_success, errors=errors)

    @classmethod
    def clean_billing_address(cls, billing_address):
        billing_data = {
            'billing_first_name': billing_address.first_name,
            'billing_last_name': billing_address.last_name,
            'billing_address_1': billing_address.street_address_1,
            'billing_address_2': billing_address.street_address_2,
            'billing_city': billing_address.city,
            'billing_postcode': billing_address.postal_code,
            'billing_country_code': billing_address.country,
            'billing_country_area': billing_address.country_area}
        return billing_data

    @classmethod
    def get_extra_info(cls, info):
        client_ip = info.context.META['REMOTE_ADDR']
        x_forwarded_for = info.context.META.get('HTTP_X_FORWARDED_FOR')
        user_agent = info.context.META.get('HTTP_USER_AGENT')
        customer_ip = x_forwarded_for if x_forwarded_for else client_ip
        return {
            'customer_ip_address': customer_ip,
            'customer_user_agent': user_agent}


class PaymentMethodCharge(BaseMutation):

    class Arguments:
        payment_method_id = graphene.ID(
            required=True, description='Payment method ID')
        amount = graphene.Argument(
            Decimal, description='Transaction amount')

    payment_method = graphene.Field(
        PaymentMethod, description='Updated payment method')


    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, payment_method_id, amount=None):
        errors = []
        payment_method = cls.get_node_or_error(
            info, payment_method_id, errors, 'payment_method_id',
            only_type=PaymentMethod)

        if not payment_method:
            return PaymentMethodCharge(errors=errors)

        try:
            gateway_charge(payment_method, amount=amount)
        except PaymentError as exc:
            msg = str(exc)
            cls.add_error(field='payment_method_id', message=msg, errors=errors)

        return PaymentMethodCharge(payment_method=payment_method, errors=errors)
