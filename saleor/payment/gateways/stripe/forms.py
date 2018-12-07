from django import forms
from django.forms.utils import flatatt
from django.forms.widgets import HiddenInput
from django.utils.html import format_html
from django.utils.translation import pgettext_lazy

from ...forms import PaymentForm
from .utils import get_amount_for_stripe

CHECKOUT_SCRIPT_URL = 'https://checkout.stripe.com/checkout.js'
CHECKOUT_DESCRIPTION = pgettext_lazy(
    'Stripe payment gateway description', 'Total payment')


class StripeCheckoutWidget(HiddenInput):

    def __init__(self, payment, gateway_params, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        kwargs['attrs'] = {
            'class': 'stripe-button',
            'src': CHECKOUT_SCRIPT_URL,
            'data-key': gateway_params.get('public_key'),
            'data-amount': get_amount_for_stripe(
                payment.total, payment.currency),
            'data-name': gateway_params.get('store_name'),
            'data-image': gateway_params.get('store_image'),
            'data-description': CHECKOUT_DESCRIPTION,
            'data-currency': payment.currency,
            'data-locale': gateway_params.get('local'),
            'data-allow-remember-me': gateway_params.get('remember_me'),
            'data-billing-address': 'true' if gateway_params.get(
                'enable_billing_address') else 'false',
            'data-zip-code': 'true' if gateway_params.get(
                'enable_billing_address') else 'false',
            'data-shipping-address': 'true' if gateway_params.get(
                'enable_shipping_address') else 'false'
        }

        if gateway_params.get('prefill'):
            kwargs['attrs'].update({
                'data-email': payment.billing_email})

        kwargs['attrs'].update(attrs)
        super(StripeCheckoutWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs.update(self.attrs)
        del attrs['id']
        return format_html('<script{0}></script>', flatatt(attrs))


class StripePaymentModalForm(PaymentForm):
    """
    At this moment partial-payment is not supported, but there is no need to
    validate amount, which may be manually adjusted in the template,
    since checkout.js can do that automatically.
    """
    stripeToken = forms.CharField(
        required=True, widget=HiddenInput)

    def __init__(self, *args, **kwargs):
        super(StripePaymentModalForm, self).__init__(*args, **kwargs)

        self.fields['stripe'] = forms.CharField(
            widget=StripeCheckoutWidget(
                payment=self.payment, gateway_params=self.gateway_params),
            required=False)

    def process_payment(self):
        cleaned_data = super(StripePaymentModalForm, self).clean()
        stripe_token = cleaned_data['stripeToken']
        self.payment.charge(payment_token=stripe_token)
        return self.payment
