from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.shortcuts import get_object_or_404
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_prices.forms import PriceField
from payments import PaymentError, PaymentStatus
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...discount.models import Voucher
from ...order import OrderStatus
from ...order.models import DeliveryGroup, Order, OrderedItem, OrderNote
from ...order.utils import cancel_order, cancel_delivery_group
from ...product.models import ProductVariant, Stock


class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = OrderNote
        fields = ['content']
        widgets = {'content': forms.Textarea({
            'rows': 5,
            'placeholder': pgettext_lazy(
                'Order note form placeholder', 'Note')})}

    def __init__(self, *args, **kwargs):
        super(OrderNoteForm, self).__init__(*args, **kwargs)


class ManagePaymentForm(forms.Form):
    amount = PriceField(
        label=pgettext_lazy(
            'Payment management form (capture, refund, release)', 'Amount'),
        max_digits=12, decimal_places=2, currency=settings.DEFAULT_CURRENCY)

    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment')
        super(ManagePaymentForm, self).__init__(*args, **kwargs)


class CapturePaymentForm(ManagePaymentForm):
    def clean(self):
        if self.payment.status != PaymentStatus.PREAUTH:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Payment form error',
                    'Only pre-authorized payments can be captured'))

    def capture(self):
        amount = self.cleaned_data['amount']
        try:
            self.payment.capture(amount.gross)
        except (PaymentError, ValueError) as e:
            self.add_error(
                None,
                pgettext_lazy(
                    'Payment form error',
                    'Payment gateway error: %s') % e.message)
            return False
        return True


class RefundPaymentForm(ManagePaymentForm):
    def clean(self):
        if self.payment.status != PaymentStatus.CONFIRMED:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Payment form error',
                    'Only confirmed payments can be refunded'))

    def refund(self):
        amount = self.cleaned_data['amount']
        try:
            self.payment.refund(amount.gross)
        except (PaymentError, ValueError) as e:
            self.add_error(
                None,
                pgettext_lazy(
                    'Payment form error',
                    'Payment gateway error: %s') % e.message)
            return False
        return True


class ReleasePaymentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment')
        super(ReleasePaymentForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.payment.status != PaymentStatus.PREAUTH:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Payment form error',
                    'Only pre-authorized payments can be released'))

    def release(self):
        try:
            self.payment.release()
        except (PaymentError, ValueError) as e:
            self.add_error(
                None,
                pgettext_lazy(
                    'Payment form error',
                    'Payment gateway error: %s') % e.message)
            return False
        return True


class MoveItemsForm(forms.Form):
    NEW_SHIPMENT = 'new'
    quantity = QuantityField(
        label=pgettext_lazy('Move items form label', 'Quantity'),
        validators=[MinValueValidator(1)])
    target_group = forms.ChoiceField(
        label=pgettext_lazy('Move items form label', 'Target shipment'))

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        super(MoveItemsForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].validators.append(
            MaxValueValidator(self.item.quantity))
        self.fields['quantity'].widget.attrs.update({
            'max': self.item.quantity, 'min': 1})
        self.fields['target_group'].choices = self.get_delivery_group_choices()

    def get_delivery_group_choices(self):
        group = self.item.delivery_group
        groups = group.order.groups.exclude(pk=group.pk).exclude(
            status='cancelled')
        choices = [(self.NEW_SHIPMENT, pgettext_lazy(
            'Delivery group value for `target_group` field',
            'New shipment'))]
        choices.extend([(g.pk, str(g)) for g in groups])
        return choices

    def move_items(self):
        how_many = self.cleaned_data['quantity']
        choice = self.cleaned_data['target_group']
        old_group = self.item.delivery_group
        if choice == self.NEW_SHIPMENT:
            # For new group we use the same delivery name but zero price
            target_group = old_group.order.groups.create(
                status=old_group.status,
                shipping_method_name=old_group.shipping_method_name)
        else:
            target_group = DeliveryGroup.objects.get(pk=choice)
        OrderedItem.objects.move_to_group(self.item, target_group, how_many)
        return target_group


class CancelItemsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        super(CancelItemsForm, self).__init__(*args, **kwargs)

    def cancel_item(self):
        if self.item.stock:
            Stock.objects.deallocate_stock(self.item.stock, self.item.quantity)
        order = self.item.delivery_group.order
        self.item.quantity = 0
        OrderedItem.objects.remove_empty_groups(self.item)
        Order.objects.recalculate_order(order)


class ChangeQuantityForm(forms.ModelForm):
    quantity = QuantityField(
        label=pgettext_lazy('Change quantity form label', 'Quantity'),
        validators=[MinValueValidator(1)])

    class Meta:
        model = OrderedItem
        fields = ['quantity']

    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant')
        super(ChangeQuantityForm, self).__init__(*args, **kwargs)
        self.initial_quantity = self.instance.quantity
        self.fields['quantity'].initial = self.initial_quantity

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        delta = quantity - self.initial_quantity
        try:
            self.variant.check_quantity(delta)
        except InsufficientStock as e:
            raise forms.ValidationError(
                npgettext_lazy(
                    'Change quantity form error',
                    'Only %(remaining)d remaining in stock.',
                    'Only %(remaining)d remaining in stock.',
                    'remaining') % {'remaining': e.item.get_stock_quantity()})
        return quantity

    def save(self):
        quantity = self.cleaned_data['quantity']
        stock = self.instance.stock
        if stock is not None:
            # update stock allocation
            delta = quantity - self.initial_quantity
            Stock.objects.allocate_stock(stock, delta)
        self.instance.change_quantity(quantity)
        Order.objects.recalculate_order(self.instance.delivery_group.order)


class ShipGroupForm(forms.ModelForm):
    class Meta:
        model = DeliveryGroup
        fields = ['tracking_number']

    def __init__(self, *args, **kwargs):
        super(ShipGroupForm, self).__init__(*args, **kwargs)
        self.fields['tracking_number'].widget.attrs.update(
            {'placeholder': pgettext_lazy(
                'Ship group form field placeholder',
                'Parcel tracking number')})

    def clean(self):
        if self.instance.status != OrderStatus.NEW:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Ship group form error',
                    'Cannot ship this group'),
                code='invalid')

    def save(self):
        order = self.instance.order
        for line in self.instance.items.all():
            stock = line.stock
            if stock is not None:
                # remove and deallocate quantity
                Stock.objects.decrease_stock(stock, line.quantity)
        self.instance.change_status(OrderStatus.SHIPPED)
        statuses = [g.status for g in order.groups.all()]
        if OrderStatus.SHIPPED in statuses and OrderStatus.NEW not in statuses:
            order.change_status(OrderStatus.SHIPPED)


class CancelGroupForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.delivery_group = kwargs.pop('delivery_group')
        super(CancelGroupForm, self).__init__(*args, **kwargs)

    def cancel_group(self):
        cancel_delivery_group(self.delivery_group)


class CancelOrderForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super(CancelOrderForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(CancelOrderForm, self).clean()
        if not self.order.can_cancel():
            raise forms.ValidationError(
                pgettext_lazy(
                    'Cancel order form error',
                    'This order can\'t be cancelled'))
        return data

    def cancel_order(self):
        cancel_order(self.order)


class RemoveVoucherForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super(RemoveVoucherForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(RemoveVoucherForm, self).clean()
        if not self.order.voucher:
            raise forms.ValidationError(
                pgettext_lazy(
                    'Remove voucher form error',
                    'This order has no voucher'))
        return data

    def remove_voucher(self):
        self.order.discount_amount = 0
        self.order.discount_name = ''
        voucher = self.order.voucher
        Voucher.objects.decrease_usage(voucher)
        self.order.voucher = None
        Order.objects.recalculate_order(self.order)


ORDER_STATUS_CHOICES = [
    ('', pgettext_lazy('Order status field value', 'All'))
] + OrderStatus.CHOICES


PAYMENT_STATUS_CHOICES = [
    ('', pgettext_lazy('Payment status field value', 'All')),
] + PaymentStatus.CHOICES


class OrderFilterForm(forms.Form):
    status = forms.ChoiceField(choices=ORDER_STATUS_CHOICES)


class PaymentFilterForm(forms.Form):
    status = forms.ChoiceField(choices=PAYMENT_STATUS_CHOICES)
