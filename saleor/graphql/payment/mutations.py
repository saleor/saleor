import graphene
from ..core.mutations import BaseMutation
from ..core.types.common import Decimal
from .types import PaymentGatewayEnum
from ...payment.utils import create_payment_method, gateway_authorize

class BraintreeBillingAddressInput(graphene.InputObjectType):
    company = graphene.String(description='Company name')
    country_code_alpha2 = graphene.String(description='2 letter ountry code')
    country_name = graphene.String(desccription='Country name')
    first_name = graphene.String(desccription='First name')
    last_name = graphene.String(desccription='Last name')
    locality = graphene.String(desccription='Locality/city')
    postal_code = graphene.String(desccription='Postal code')
    street_address = graphene.String(desccription='Street address')


class BraintreeCustomerInput(graphene.InputObjectType):
    company = graphene.String(description='Company name')
    email = graphene.String(description='Email')


class CompleteCheckoutWithCreditCard(BaseMutation):
    class Arguments:
        gateway = PaymentGatewayEnum()
        transaction_token = graphene.Argument(
            graphene.String,
            required=True,
            description='One time transaction token')
        amount = graphene.Argument(
            Decimal, required=True, description='Transaction amount')
        store_payment_method = graphene.Argument(
            graphene.Boolean,
            default_value=False,
            description='Store card as payment method')

    transaction_id = graphene.String()
    transaction_status = graphene.String()
    transaction_rejection_reason = graphene.String()

    class Meta:
        description = 'Creates credit card transaction.'

    def mutate(
            self,
            info,
            client_token,
            amount,
            store_payment_method,
            billing_address=None,
            customer=None):

        # create payment method
        payment_method = create_payment_method(

        )
        # authorize payment
        transaction = gateway_authorize(payment_method)

        return CompleteCheckoutWithCreditCard(
            transaction_id='',
            transaction_status='',
            transaction_rejection_reason='')


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
