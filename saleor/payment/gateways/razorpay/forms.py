
from django import forms
from django.forms.utils import flatatt
from django.forms.widgets import HiddenInput
from django.utils.html import format_html
from django.utils.translation import pgettext_lazy

from ...forms import PaymentForm

CHECKOUT_SCRIPT_URL = 'https://checkout.razorpay.com/v1/checkout.js'

PRIMARY_BTN_TEXT = pgettext_lazy(
    'Rozorpay payment gateway primary button', 'Pay now with Razorpay')
SECONDARY_TITLE = pgettext_lazy(
    'Rozorpay payment gateway secondary title', 'Total payment')


class RazorPayCheckoutWidget(HiddenInput):
    def __init__(
            self,
            *, payment,
            public_key, prefill, store_name, store_image,
            **kwargs):
        override_attrs = kwargs.get('attrs', None)
        base_attrs = kwargs['attrs'] = {
            'src': CHECKOUT_SCRIPT_URL,
            'data-key': public_key,
            'data-buttontext': PRIMARY_BTN_TEXT,
            'data-image': store_image,
            'data-name': store_name,
            'data-description': SECONDARY_TITLE,
            'data-amount': int(payment.total * 100),
            'data-currency': payment.currency
        }

        if prefill:
            customer_name = '%s %s' % (
                payment.billing_last_name,
                payment.billing_first_name)
            base_attrs.update({
                'data-prefill.name': customer_name,
                'data-prefill.email': payment.billing_email
            })

        if override_attrs:
            base_attrs.update(override_attrs)
        super().__init__(attrs=base_attrs)

    def render(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.update(self.attrs)
        return format_html('<script{0}></script>', flatatt(attrs))


class RazorPaymentForm(PaymentForm):
    razorpay_payment_id = forms.CharField(
        required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widget = RazorPayCheckoutWidget(
            payment=self.payment, **self.gateway_params)
        self.fields['razorpay'] = forms.CharField(
            widget=widget, required=False)

    def process_payment(self):
        data = super(RazorPaymentForm, self).clean()
        transaction_id = data['razorpay_payment_id']
        self.payment.charge(transaction_id)
        return self.payment
