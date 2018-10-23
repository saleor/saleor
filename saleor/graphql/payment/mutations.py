import graphene
from django.conf import settings
from graphql_jwt.decorators import permission_required
from prices import Money, TaxedMoney

from ...payment import PaymentError
from ...payment.utils import (
    create_payment, gateway_authorize, gateway_capture, gateway_refund,
    gateway_void)
from ..account.i18n import I18nMixin
from ..account.types import AddressInput
from ..checkout.types import Checkout
from ..core.mutations import BaseMutation
from ..core.types.common import Decimal
from .types import Payment, PaymentGatewayEnum


class PaymentInput(graphene.InputObjectType):
    gateway = PaymentGatewayEnum()
    checkout_id = graphene.ID(description='Checkout ID.')
    transaction_token = graphene.String(
        required=True, description='One time transaction token.')
    amount = Decimal(
        required=True,
        description=(
            'Total amount of the transaction, including '
            'all taxes and discounts.'))
    billing_address = AddressInput(description='Billing address')


class CheckoutPaymentCreate(BaseMutation, I18nMixin):
    payment = graphene.Field(Payment, description='Updated payment')

    class Arguments:
        input = PaymentInput(required=True, description='Payment details')

    class Meta:
        description = 'Creates credit card transaction.'

    @classmethod
    def mutate(cls, root, info, input):
        # FIXME: improve error handling
        errors = []
        checkout = cls.get_node_or_error(
            info,
            input['checkout_id'],
            errors,
            'checkout_id',
            only_type=Checkout)
        if not checkout:
            return CheckoutPaymentCreate(errors=errors)
        billing_data = {}
        if input['billing_address']:
            billing_address, errors = cls.validate_address(
                input['billing_address'], errors, 'billing_address')
            if not billing_address:
                return CheckoutPaymentCreate(errors=errors)
            billing_data = cls.clean_billing_address(billing_address)
        extra_data = cls.get_extra_info(info)
        gross = Money(input['amount'], currency=settings.DEFAULT_CURRENCY)
        payment = create_payment(
            total=gross,
            variant=input['gateway'],
            billing_email=checkout.email,
            extra_data=extra_data,
            checkout=checkout,
            **billing_data)

        # authorize payment
        try:
            gateway_authorize(payment, input['transaction_token'])
        except PaymentError as exc:
            msg = str(exc)
            cls.add_error(field=None, message=msg, errors=errors)

        return CheckoutPaymentCreate(payment=payment, errors=errors)

    @classmethod
    def clean_billing_address(cls, billing_address):
        billing_data = {
            'billing_first_name': billing_address.first_name,
            'billing_last_name': billing_address.last_name,
            'billing_company_name': billing_address.company_name,
            'billing_address_1': billing_address.street_address_1,
            'billing_address_2': billing_address.street_address_2,
            'billing_city': billing_address.city,
            'billing_postal_code': billing_address.postal_code,
            'billing_country_code': billing_address.country.code,
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


class PaymentCapture(BaseMutation):
    payment = graphene.Field(Payment, description='Updated payment')

    class Arguments:
        payment_id = graphene.ID(required=True, description='Payment ID')
        amount = Decimal(description='Transaction amount')

    class Meta:
        description = 'Captures the authorized payment amount'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, payment_id, amount=None):
        errors = []
        payment = cls.get_node_or_error(
            info, payment_id, errors, 'payment_id', only_type=Payment)

        if not payment:
            return PaymentCapture(errors=errors)

        try:
            gateway_capture(payment, amount)
        except PaymentError as exc:
            msg = str(exc)
            cls.add_error(field=None, message=msg, errors=errors)
        return PaymentCapture(payment=payment, errors=errors)


class PaymentRefund(PaymentCapture):
    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, payment_id, amount=None):
        errors = []
        payment = cls.get_node_or_error(
            info, payment_id, errors, 'payment_id', only_type=Payment)

        if not payment:
            return PaymentRefund(errors=errors)

        try:
            gateway_refund(payment, amount=amount)
        except PaymentError as exc:
            msg = str(exc)
            cls.add_error(field=None, message=msg, errors=errors)
        return PaymentRefund(payment=payment, errors=errors)

    class Meta:
        description = 'Refunds the captured payment amount'


class PaymentVoid(BaseMutation):
    payment = graphene.Field(Payment, description='Updated payment')

    class Arguments:
        payment_id = graphene.ID(required=True, description='Payment ID')

    class Meta:
        description = 'Voids the authorized payment'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, payment_id, amount=None):
        errors = []
        payment = cls.get_node_or_error(
            info, payment_id, errors, 'payment_id', only_type=Payment)

        if not payment:
            return PaymentVoid(errors=errors)

        try:
            gateway_void(payment)
        except PaymentError as exc:
            msg = str(exc)
            cls.add_error(field=None, message=msg, errors=errors)
        return PaymentVoid(payment=payment, errors=errors)
