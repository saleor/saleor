import graphene
from ..core.mutations import BaseMutation
from ..core.types.common import Decimal, Error
from .types import PaymentGatewayEnum
from ...payment import PaymentError
from ...payment.utils import create_payment_method, gateway_authorize
from ..account.types import AddressInput

class CompleteCheckoutWithCreditCard(BaseMutation):
    class Arguments:
        gateway = PaymentGatewayEnum()
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
            description='Store card as payment method')

    transaction_id = graphene.String()
    transaction_success = graphene.String()

    class Meta:
        description = 'Creates credit card transaction.'

    def mutate(
            self,
            info,
            gateway,
            transaction_token,
            amount,
            store_payment_method,
            billing_address=None):
        # FIXME: This mutation should also fetch cart

        client_ip = info.context.META['REMOTE_ADDR']
        x_forwarded_for = info.context.META.get('HTTP_X_FORWARDED_FOR')
        user_agent = info.context.META['HTTP_USER_AGENT']

        extra_data = {
            'customer_ip_address': x_forwarded_for if x_forwarded_for else client_ip,
            'customer_user_agent': user_agent
        }
        billing_data = {}
        if billing_address:
            billing_data = {
                'billing_first_name': billing_address.first_name,
                'billing_last_name': billing_address.last_name,
                'billing_address_1': billing_address.street_address_1,
                'billing_address_2': billing_address.street_address_2,
                'billing_city': billing_address.city,
                'billing_postcide': billing_address.postal_code,
                'billing_country_code': billing_address.country,
                'billing_country_area': billing_address.country_area}
        # create payment method
        payment_method = create_payment_method(
            variant=gateway,
            billing_email='',
            extra_data=extra_data,
            total=amount,
            **billing_data)
        # authorize payment
        try:
            transaction = gateway_authorize(payment_method, transaction_token)
        except PaymentError as exc:
            field = 'transaction_token'
            msg = str(exc)
            return CompleteCheckoutWithCreditCard(
               errors=[Error(field=field, message=msg)])

        return CompleteCheckoutWithCreditCard(
            transaction_id=transaction.token,
            transaction_success=transaction.is_success)


# class PaymentMethodCreate(BaseMutation):
#     pass

# class PaymentMethodUpdate(BaseMutation):
#     pass

# class PaymentMethodDelete(BaseMutation):
#     pass

# class TransactionRefund(BaseMutation):
#     pass

# class TransactionVoid(BaseMutation):
#     pass

# class PaymentMethodNonceCreate(BaseMutation):
#     pass
