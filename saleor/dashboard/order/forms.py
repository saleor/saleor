from django import forms
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.urls import reverse, reverse_lazy
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_prices.forms import PriceField
from payments import PaymentError, PaymentStatus
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...core.utils import build_absolute_uri
from ...discount.utils import decrease_voucher_usage
from ...order import GroupStatus
from ...order.emails import send_note_confirmation
from ...order.models import DeliveryGroup, OrderLine, OrderNote
from ...order.utils import (
    add_variant_to_delivery_group, cancel_order, change_order_line_quantity,
    merge_duplicates_into_order_line, move_order_line_to_group,
    recalculate_order, remove_empty_groups)
from ...product.models import Product, ProductVariant, Stock
from ...product.utils import allocate_stock, deallocate_stock
from ...userprofile.i18n import (
    AddressForm as StorefrontAddressForm, PossiblePhoneNumberFormField)
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
        email = order.get_user_current_email()
        url = build_absolute_uri(
            reverse(
                'order:details', kwargs={'token': order.token}))
        send_note_confirmation.delay(email, url)


class ManagePaymentForm(forms.Form):
    amount = PriceField(
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
                'Payment form error',
                'Payment gateway error: %s') % message)

    def try_payment_action(self, action):
        amount = self.cleaned_data['amount']
        try:
            action(amount.gross)
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


class MoveLinesForm(forms.Form):
    """Allows splitting an order line into an existing or new group."""

    quantity = QuantityField(
        label=pgettext_lazy('Move lines form label', 'Quantity'),
        validators=[MinValueValidator(1)])
    target_group = forms.ModelChoiceField(
        queryset=DeliveryGroup.objects.none(), required=False,
        empty_label=pgettext_lazy(
            'Shipment group value for `target_group` field', 'New shipment'),
        label=pgettext_lazy('Move lines form label', 'Target shipment'))

    def __init__(self, *args, **kwargs):
        self.line = kwargs.pop('line')
        super().__init__(*args, **kwargs)
        self.fields['quantity'].validators.append(
            MaxValueValidator(self.line.quantity))
        self.fields['quantity'].widget.attrs.update({
            'max': self.line.quantity, 'min': 1})
        self.old_group = self.line.delivery_group
        queryset = self.old_group.order.groups.exclude(
            pk=self.old_group.pk).exclude(status=GroupStatus.CANCELLED)
        self.fields['target_group'].queryset = queryset

    def move_lines(self):
        how_many = self.cleaned_data.get('quantity')
        target_group = self.cleaned_data.get('target_group')
        if not target_group:
            # For new group we use the same shipping name but zero price
            target_group = self.old_group.order.groups.create(
                status=self.old_group.status,
                shipping_method_name=self.old_group.shipping_method_name)
        move_order_line_to_group(self.line, target_group, how_many)
        return target_group


class CancelOrderLineForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.line = kwargs.pop('line')
        super().__init__(*args, **kwargs)

    def cancel_line(self):
        if self.line.stock:
            deallocate_stock(self.line.stock, self.line.quantity)
        order = self.line.delivery_group.order
        self.line.quantity = 0
        remove_empty_groups(self.line)
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
        return quantity

    def save(self):
        quantity = self.cleaned_data['quantity']
        stock = self.instance.stock
        if stock is not None:
            # update stock allocation
            delta = quantity - self.initial_quantity
            allocate_stock(stock, delta)
        change_order_line_quantity(self.instance, quantity)
        recalculate_order(self.instance.delivery_group.order)
        return self.instance


class ShipGroupForm(forms.ModelForm):
    """Dispatch a group and optionally assigns a tracking number.

    This process involves permanently decreasing the previously allocated
    stock.
    """

    class Meta:
        model = DeliveryGroup
        fields = ['tracking_number']
        labels = {
            'tracking_number': pgettext_lazy(
                'Shipment tracking number', 'Tracking number')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tracking_number'].widget.attrs.update(
            {'placeholder': pgettext_lazy(
                'Ship group form field placeholder',
                'Parcel tracking number')})

    def clean(self):
        if self.instance.status != GroupStatus.NEW:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Ship group form error',
                    'Cannot ship this group'),
                code='invalid')

    def save(self, commit=True):
        self.instance.ship(self.cleaned_data.get('tracking_number'))
        return super().save(commit)


class CancelGroupForm(forms.ModelForm):
    """Allow canceling a single group in an order.

    Deallocates or increases corresponding stocks, depending whether new
    or shipped group is cancelled.
    """

    class Meta:
        model = DeliveryGroup
        fields = []

    def save(self, commit=True):
        self.instance.cancel()
        return super().save(commit)


class CancelOrderForm(forms.Form):
    """Allow canceling an entire order.

    Deallocates or increases corresponding stocks in each delivery group,
    depending whether new or shipped group is cancelled.
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


class AddVariantToDeliveryGroupForm(forms.Form):
    """Allow adding lines with given quantity to a shipment group."""

    variant = AjaxSelect2ChoiceField(
        queryset=ProductVariant.objects.filter(
            product__in=Product.objects.available_products()),
        fetch_data_url=reverse_lazy('dashboard:ajax-available-variants'))
    quantity = QuantityField(
        label=pgettext_lazy(
            'Add variant to shipment group form label', 'Quantity'),
        validators=[MinValueValidator(1)])

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.discounts = kwargs.pop('discounts')
        super().__init__(*args, **kwargs)

    def clean(self):
        """Check if given quantity is available in stocs."""
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
        """Add variant to target group.

        Updates stocks and order.
        """
        variant = self.cleaned_data.get('variant')
        quantity = self.cleaned_data.get('quantity')
        add_variant_to_delivery_group(
            self.group, variant, quantity, self.discounts)
        recalculate_order(self.group.order)


class AddressForm(StorefrontAddressForm):
    phone = PossiblePhoneNumberFormField(
        widget=PhonePrefixWidget, required=False)
