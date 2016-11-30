from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from django_prices.forms import PriceField
from payments import PaymentError
from payments.models import PAYMENT_STATUS_CHOICES
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...discount.models import Voucher
from ...order import Status
from ...order.models import DeliveryGroup, Order, OrderedItem, OrderNote
from ...product.models import ProductVariant, Stock


class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = OrderNote
        fields = ['content']
        widgets = {'content': forms.Textarea({
            'rows': 5, 'placeholder': _('Note')})}

    def __init__(self, *args, **kwargs):
        super(OrderNoteForm, self).__init__(*args, **kwargs)


class ManagePaymentForm(forms.Form):
    amount = PriceField(max_digits=12, decimal_places=2,
                        currency=settings.DEFAULT_CURRENCY)

    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment')
        super(ManagePaymentForm, self).__init__(*args, **kwargs)


class CapturePaymentForm(ManagePaymentForm):
    def clean(self):
        if self.payment.status != 'preauth':
            raise forms.ValidationError(
                _('Only pre-authorized payments can be captured'))

    def capture(self):
        amount = self.cleaned_data['amount']
        try:
            self.payment.capture(amount.gross)
        except (PaymentError, ValueError) as e:
            self.add_error(None, _('Payment gateway error: %s') % e.message)
            return False
        return True


class RefundPaymentForm(ManagePaymentForm):
    def clean(self):
        if self.payment.status != 'confirmed':
            raise forms.ValidationError(
                _('Only confirmed payments can be refunded'))

    def refund(self):
        amount = self.cleaned_data['amount']
        try:
            self.payment.refund(amount.gross)
        except (PaymentError, ValueError) as e:
            self.add_error(None, _('Payment gateway error: %s') % e.message)
            return False
        return True


class ReleasePaymentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment')
        super(ReleasePaymentForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.payment.status != 'preauth':
            raise forms.ValidationError(
                _('Only pre-authorized payments can be released'))

    def release(self):
        try:
            self.payment.release()
        except (PaymentError, ValueError) as e:
            self.add_error(None, _('Payment gateway error: %s') % e.message)
            return False
        return True


class MoveItemsForm(forms.Form):
    quantity = QuantityField(label=_('Quantity'))
    target_group = forms.ChoiceField(label=_('Target shipment'))

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        super(MoveItemsForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs.update({
            'max': self.item.quantity, 'min': 1})
        self.fields['target_group'].choices = self.get_delivery_group_choices()

    def get_delivery_group_choices(self):
        group = self.item.delivery_group
        groups = group.order.groups.exclude(pk=group.pk).exclude(
            status='cancelled')
        choices = [('new', _('New shipment'))]
        choices.extend([(g.pk, str(g)) for g in groups])
        return choices

    def move_items(self):
        how_many = self.cleaned_data['quantity']
        choice = self.cleaned_data['target_group']
        old_group = self.item.delivery_group
        if choice == 'new':
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
        OrderedItem.objects.remove_empty_groups(self.item, force=True)
        Order.objects.recalculate_order(order)


class ChangeQuantityForm(forms.ModelForm):
    class Meta:
        model = OrderedItem
        fields = ['quantity']

    def __init__(self, *args, **kwargs):
        super(ChangeQuantityForm, self).__init__(*args, **kwargs)
        self.initial_quantity = self.instance.quantity
        self.fields['quantity'].widget.attrs.update({'min': 1})
        self.fields['quantity'].initial = self.initial_quantity

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        delta = quantity - self.initial_quantity
        variant = get_object_or_404(
            ProductVariant, sku=self.instance.product_sku)
        try:
            variant.check_quantity(delta)
        except InsufficientStock as e:
            raise forms.ValidationError(
                _('Only %(remaining)d remaining in stock.') % {
                    'remaining': e.item.get_stock_quantity()})
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
            {'placeholder': _('Parcel tracking number')})

    def clean(self):
        if self.instance.status != 'new':
            raise forms.ValidationError(_('Cannot ship this group'),
                                        code='invalid')

    def save(self):
        order = self.instance.order
        for line in self.instance.items.all():
            stock = line.stock
            if stock is not None:
                # remove and deallocate quantity
                Stock.objects.decrease_stock(stock, line.quantity)
        self.instance.change_status('shipped')
        statuses = [g.status for g in order.groups.all()]
        if 'shipped' in statuses and 'new' not in statuses:
            order.change_status('shipped')


class CancelGroupForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.delivery_group = kwargs.pop('delivery_group')
        super(CancelGroupForm, self).__init__(*args, **kwargs)

    def cancel_group(self):
        for line in self.delivery_group:
            if line.stock:
                Stock.objects.deallocate_stock(line.stock, line.quantity)
        self.delivery_group.status = Status.CANCELLED
        self.delivery_group.save()
        other_groups = self.delivery_group.order.groups.all()
        statuses = set(other_groups.values_list('status', flat=True))
        if statuses == {Status.CANCELLED}:
            # Cancel whole order
            self.delivery_group.order.status = Status.CANCELLED
            self.delivery_group.order.save(update_fields=['status'])


class CancelOrderForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super(CancelOrderForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(CancelOrderForm, self).clean()
        if not self.order.can_cancel():
            raise forms.ValidationError(_('This order can\'t be cancelled'))
        return data

    def cancel_order(self):
        for group in self.order.groups.all():
            group_form = CancelGroupForm(delivery_group=group)
            group_form.cancel_group()


class RemoveVoucherForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super(RemoveVoucherForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(RemoveVoucherForm, self).clean()
        if not self.order.voucher:
            raise forms.ValidationError(_('This order has no voucher'))
        return data

    def remove_voucher(self):
        self.order.discount_amount = 0
        self.order.discount_name = ''
        voucher = self.order.voucher
        Voucher.objects.decrease_usage(voucher)
        self.order.voucher = None
        Order.objects.recalculate_order(self.order)

ORDER_STATUS_CHOICES = [('', pgettext_lazy('Order status field value',
                                           'All'))] + Status.CHOICES

PAYMENT_STATUS_CHOICES = (('', pgettext_lazy('Payment status field value',
                                             'All')),) + PAYMENT_STATUS_CHOICES


class OrderFilterForm(forms.Form):
    status = forms.ChoiceField(choices=ORDER_STATUS_CHOICES)


class PaymentFilterForm(forms.Form):
    status = forms.ChoiceField(choices=PAYMENT_STATUS_CHOICES)
