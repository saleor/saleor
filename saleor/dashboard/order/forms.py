from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse_lazy
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_prices.forms import PriceField
from payments import PaymentError, PaymentStatus
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...core.forms import AjaxSelect2ChoiceField
from ...discount.models import Voucher
from ...order import OrderStatus
from ...order.models import DeliveryGroup, Order, OrderLine, OrderNote
from ...order.utils import (
    add_variant_to_delivery_group, cancel_order, cancel_delivery_group,
    change_order_line_quantity, merge_duplicated_lines)
from ...product.models import Product, ProductVariant, Stock


class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = OrderNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea()
        }

    def __init__(self, *args, **kwargs):
        super(OrderNoteForm, self).__init__(*args, **kwargs)


class ManagePaymentForm(forms.Form):
    amount = PriceField(
        label=pgettext_lazy(
            'Payment management form (capture, refund, release)', 'Amount'),
        max_digits=12,
        decimal_places=2,
        currency=settings.DEFAULT_CURRENCY)

    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment')
        super(ManagePaymentForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.payment.status != self.clean_status:
            raise forms.ValidationError(self.clean_error)

    def payment_error(self, message):
        self.add_error(None,
                       pgettext_lazy('Payment form error',
                                     'Payment gateway error: %s') % message)

    def try_payment_action(self, action):
        amount = self.cleaned_data['amount']
        try:
            action(amount.gross)
        except (PaymentError, ValueError) as e:
            self.payment_error(e.message)
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
    clean_error = pgettext_lazy('Payment form error',
                                'Only pre-authorized payments can be released')

    def release(self):
        return self.try_payment_action(self.payment.release)


class MoveLinesForm(forms.Form):
    """ Moves part of products in order line to existing or new group.  """
    quantity = QuantityField(
        label=pgettext_lazy('Move lines form label', 'Quantity'),
        validators=[MinValueValidator(1)])
    target_group = forms.ModelChoiceField(
        queryset=DeliveryGroup.objects.none(), required=False,
        empty_label=pgettext_lazy(
            'Delivery group value for `target_group` field',
            'New shipment'),
        label=pgettext_lazy('Move lines form label', 'Target shipment'))

    def __init__(self, *args, **kwargs):
        self.line = kwargs.pop('line')
        super(MoveLinesForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].validators.append(
            MaxValueValidator(self.line.quantity))
        self.fields['quantity'].widget.attrs.update({
            'max': self.line.quantity, 'min': 1})
        self.old_group = self.line.delivery_group
        queryset = self.old_group.order.groups.exclude(
            pk=self.old_group.pk).exclude(status=OrderStatus.CANCELLED)
        self.fields['target_group'].queryset = queryset

    def move_lines(self):
        how_many = self.cleaned_data.get('quantity')
        target_group = self.cleaned_data.get('target_group')
        if not target_group:
            # For new group we use the same delivery name but zero price
            target_group = self.old_group.order.groups.create(
                status=self.old_group.status,
                shipping_method_name=self.old_group.shipping_method_name)
        OrderLine.objects.move_to_group(self.line, target_group, how_many)
        return target_group


class CancelLinesForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.line = kwargs.pop('line')
        super(CancelLinesForm, self).__init__(*args, **kwargs)

    def cancel_line(self):
        if self.line.stock:
            Stock.objects.deallocate_stock(self.line.stock, self.line.quantity)
        order = self.line.delivery_group.order
        self.line.quantity = 0
        OrderLine.objects.remove_empty_groups(self.line)
        Order.objects.recalculate_order(order)


class ChangeQuantityForm(forms.ModelForm):
    quantity = QuantityField(
        label=pgettext_lazy('Change quantity form label', 'Quantity'),
        validators=[MinValueValidator(1)])

    class Meta:
        model = OrderLine
        fields = ['quantity']

    def __init__(self, *args, **kwargs):
        super(ChangeQuantityForm, self).__init__(*args, **kwargs)
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
                    'remaining') % {'remaining': (
                        self.initial_quantity + stock.quantity_available)})
        return quantity

    def save(self):
        quantity = self.cleaned_data['quantity']
        stock = self.instance.stock
        if stock is not None:
            # update stock allocation
            delta = quantity - self.initial_quantity
            Stock.objects.allocate_stock(stock, delta)
        change_order_line_quantity(self.instance, quantity)
        Order.objects.recalculate_order(self.instance.delivery_group.order)
        return self.instance


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

    def __init__(self, *args, **kwargs):
        super(ChangeStockForm, self).__init__(*args, **kwargs)
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
        if self.old_stock is not None:
            Stock.objects.deallocate_stock(self.old_stock, quantity)
        stock = self.instance.stock
        if stock is not None:
            self.instance.stock_location = (
                stock.location.name if stock.location else '')
            Stock.objects.allocate_stock(stock, quantity)
        super(ChangeStockForm, self).save(commit)
        merge_duplicated_lines(self.instance)
        return self.instance


class AddVariantToDeliveryGroupForm(forms.Form):
    """ Adds variant in given quantity to delivery group. """
    variant = AjaxSelect2ChoiceField(
        queryset=ProductVariant.objects.filter(
            product__in=Product.objects.get_available_products()),
        fetch_data_url=reverse_lazy('dashboard:ajax-available-variants'))
    quantity = QuantityField(
        label=pgettext_lazy(
            'Add variant to delivery group form label', 'Quantity'),
        validators=[MinValueValidator(1)])

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        super(AddVariantToDeliveryGroupForm, self).__init__(*args, **kwargs)

    def clean(self):
        """ Checks if given quantity is available in stocks. """
        cleaned_data = super(AddVariantToDeliveryGroupForm, self).clean()
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
        """ Adds variant to target group. Updates stocks and order. """
        variant = self.cleaned_data.get('variant')
        quantity = self.cleaned_data.get('quantity')
        add_variant_to_delivery_group(self.group, variant, quantity)
        Order.objects.recalculate_order(self.group.order)
