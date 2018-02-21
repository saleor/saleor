from django import forms
from django.conf import settings
from django.core.validators import MinValueValidator
from django.urls import reverse_lazy
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_prices.forms import MoneyField
from payments import PaymentError, PaymentStatus

from ...account.i18n import (
    AddressForm as StorefrontAddressForm, PossiblePhoneNumberFormField)
from ...cart.forms import QuantityField
from ...core.exceptions import InsufficientStock
from ...discount.utils import decrease_voucher_usage
from ...order.emails import send_note_confirmation
from ...order.models import Fulfillment, FulfillmentLine, OrderLine, OrderNote
from ...order.utils import (
    add_variant_to_order, cancel_order, change_order_line_quantity,
    fulfill_order_line, merge_duplicates_into_order_line, recalculate_order)
from ...product.models import Product, ProductVariant, Stock
from ...product.utils import allocate_stock, deallocate_stock
from ..forms import AjaxSelect2ChoiceField
from ..widgets import PhonePrefixWidget


class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = OrderNote
        fields = ['content', 'is_public']
        widgets = {
            'content': forms.Textarea()}
        labels = {
            'content': pgettext_lazy('Order note', 'Note'),
            'is_public': pgettext_lazy(
                'Allow customers to see note toggle',
                'Customer can see this note')}

    def send_confirmation_email(self):
        order = self.instance.order
        send_note_confirmation.delay(order.pk)


class ManagePaymentForm(forms.Form):
    amount = MoneyField(
        label=pgettext_lazy(
            'Payment management form (capture, refund, release)', 'Amount'),
        max_digits=12,
        decimal_places=2,
        currency=settings.DEFAULT_CURRENCY)

    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment')
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.payment.status != self.clean_status:
            raise forms.ValidationError(self.clean_error)

    def payment_error(self, message):
        self.add_error(
            None, pgettext_lazy(
                'Payment form error', 'Payment gateway error: %s') % message)

    def try_payment_action(self, action):
        money = self.cleaned_data['amount']
        try:
            action(money.amount)
        except (PaymentError, ValueError) as e:
            self.payment_error(str(e))
            return False
        return True


class CapturePaymentForm(ManagePaymentForm):

    clean_status = PaymentStatus.PREAUTH
    clean_error = pgettext_lazy('Payment form error',
                                'Only pre-authorized payments can be captured')

    def capture(self):
        return self.try_payment_action(self.payment.capture)


class RefundPaymentForm(ManagePaymentForm):

    clean_status = PaymentStatus.CONFIRMED
    clean_error = pgettext_lazy('Payment form error',
                                'Only confirmed payments can be refunded')

    def refund(self):
        return self.try_payment_action(self.payment.refund)


class ReleasePaymentForm(ManagePaymentForm):

    clean_status = PaymentStatus.PREAUTH
    clean_error = pgettext_lazy(
        'Payment form error', 'Only pre-authorized payments can be released')

    def release(self):
        return self.try_payment_action(self.payment.release)


class CancelOrderLineForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.line = kwargs.pop('line')
        super().__init__(*args, **kwargs)

    def cancel_line(self):
        if self.line.stock:
            deallocate_stock(self.line.stock, self.line.quantity)
        order = self.line.order
        self.line.delete()
        if not order.lines.exists():
            order.create_history_entry(
                content=pgettext_lazy(
                    'Order status history entry',
                    'Order cancelled. No items in order'))
        recalculate_order(order)


class ChangeQuantityForm(forms.ModelForm):
    quantity = QuantityField(
        validators=[MinValueValidator(1)])

    class Meta:
        model = OrderLine
        fields = ['quantity']
        labels = {
            'quantity': pgettext_lazy(
                'Integer number', 'Quantity')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_quantity = self.instance.quantity
        self.fields['quantity'].initial = self.initial_quantity
        self.fields['quantity'].widget.attrs['min'] = (
            self.instance.quantity_fulfilled)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        delta = quantity - self.initial_quantity
        stock = self.instance.stock
        if stock and delta > stock.quantity_available:
            raise forms.ValidationError(
                npgettext_lazy(
                    'Change quantity form error',
                    'Only %(remaining)d remaining in stock.',
                    'Only %(remaining)d remaining in stock.',
                    'remaining') % {
                        'remaining': (
                            self.initial_quantity + stock.quantity_available)})
        if quantity < self.instance.quantity_fulfilled:
            raise forms.ValidationError(
                npgettext_lazy(
                    'Change quantity form error',
                    '%(quantity)d is already fulfilled.',
                    '%(quantity)d are already fulfilled.',
                    'quantity') % {
                        'quantity': self.instance.quantity_fulfilled})
        return quantity

    def save(self):
        quantity = self.cleaned_data['quantity']
        stock = self.instance.stock
        if stock is not None:
            # update stock allocation
            delta = quantity - self.initial_quantity
            allocate_stock(stock, delta)
        change_order_line_quantity(self.instance, quantity)
        recalculate_order(self.instance.order)
        return self.instance


class CancelOrderForm(forms.Form):
    """Allow canceling an entire order.

    Deallocates corresponding stocks for each order line.
    """

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if not self.order.can_cancel():
            raise forms.ValidationError(
                pgettext_lazy(
                    'Cancel order form error',
                    "This order can't be cancelled"))
        return data

    def cancel_order(self):
        cancel_order(self.order)


class RemoveVoucherForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if not self.order.voucher:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Remove voucher form error',
                    'This order has no voucher'))
        return data

    def remove_voucher(self):
        self.order.discount_amount = 0
        self.order.discount_name = ''
        decrease_voucher_usage(self.order.voucher)
        self.order.voucher = None
        recalculate_order(self.order)


PAYMENT_STATUS_CHOICES = (
    [('', pgettext_lazy('Payment status field value', 'All'))] +
    PaymentStatus.CHOICES)


class PaymentFilterForm(forms.Form):
    status = forms.ChoiceField(choices=PAYMENT_STATUS_CHOICES)


class StockChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.location.name


class ChangeStockForm(forms.ModelForm):
    stock = StockChoiceField(queryset=Stock.objects.none())

    class Meta:
        model = OrderLine
        fields = ['stock']
        labels = {
            'stock': pgettext_lazy(
                'Stock record', 'Stock')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sku = self.instance.product_sku
        self.fields['stock'].queryset = Stock.objects.filter(variant__sku=sku)
        self.old_stock = self.instance.stock

    def clean_stock(self):
        stock = self.cleaned_data['stock']
        if stock and stock.quantity_available < self.instance.quantity:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Change stock form error',
                    'Only %(remaining)d remaining in this stock.') % {
                        'remaining': stock.quantity_available})
        return stock

    def save(self, commit=True):
        quantity = self.instance.quantity
        stock = self.instance.stock
        self.instance.stock_location = (
            stock.location.name if stock.location else '')
        if self.old_stock:
            deallocate_stock(self.old_stock, quantity)
        allocate_stock(stock, quantity)
        super().save(commit)
        merge_duplicates_into_order_line(self.instance)
        return self.instance


class AddVariantToOrderForm(forms.Form):
    """Allow adding lines with given quantity to an order."""

    variant = AjaxSelect2ChoiceField(
        queryset=ProductVariant.objects.filter(
            product__in=Product.objects.available_products()),
        fetch_data_url=reverse_lazy('dashboard:ajax-available-variants'))
    quantity = QuantityField(
        label=pgettext_lazy(
            'Add variant to order form label', 'Quantity'),
        validators=[MinValueValidator(1)])

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        self.discounts = kwargs.pop('discounts')
        super().__init__(*args, **kwargs)

    def clean(self):
        """Check if given quantity is available in stocks."""
        cleaned_data = super().clean()
        variant = cleaned_data.get('variant')
        quantity = cleaned_data.get('quantity')
        if variant and quantity is not None:
            try:
                variant.check_quantity(quantity)
            except InsufficientStock as e:
                error = forms.ValidationError(
                    pgettext_lazy(
                        'Add item form error',
                        'Could not add item. '
                        'Only %(remaining)d remaining in stock.' %
                        {'remaining': e.item.get_stock_quantity()}))
                self.add_error('quantity', error)
        return cleaned_data

    def save(self):
        """Add variant to order.

        Updates stocks and order.
        """
        variant = self.cleaned_data.get('variant')
        quantity = self.cleaned_data.get('quantity')
        add_variant_to_order(
            self.order, variant, quantity, self.discounts)
        recalculate_order(self.order)


class AddressForm(StorefrontAddressForm):
    phone = PossiblePhoneNumberFormField(
        widget=PhonePrefixWidget, required=False)


class FulfillmentForm(forms.ModelForm):
    class Meta:
        model = Fulfillment
        fields = ['tracking_number']

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('order')
        super().__init__(*args, **kwargs)
        self.instance.order = order


class BaseFulfillmentLineFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False


class FulfillmentLineForm(forms.ModelForm):
    class Meta:
        model = FulfillmentLine
        fields = ['order_line', 'quantity']

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity == 0:
            raise forms.ValidationError(pgettext_lazy(
                'Fulfill order line form error',
                'Order line could not be fulfilled with zero quantity.'))
        return quantity

    def save(self, commit=True):
        fulfill_order_line(self.instance.order_line, self.instance.quantity)
        return super().save(commit)
