from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from django_prices.forms import PriceField
from payments import PaymentError
from payments.models import PAYMENT_STATUS_CHOICES
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...order.models import DeliveryGroup, Order, OrderedItem, OrderNote
from ...product.models import ProductVariant


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
            # For new group we are set the same delivery name but with zero price
            target_group = old_group.order.groups.create(
                status=old_group.status,
                shipping_method_name=old_group.shipping_method_name)
        else:
            target_group = DeliveryGroup.objects.get(pk=choice)
        OrderedItem.objects.move_to_group(self.item, target_group, how_many)
        return target_group


class ChangeQuantityForm(forms.ModelForm):
    class Meta:
        model = OrderedItem
        fields = ['quantity']

    def __init__(self, *args, **kwargs):
        super(ChangeQuantityForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs.update({'min': 1})
        self.fields['quantity'].initial = self.instance.quantity

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        variant = get_object_or_404(
            ProductVariant, sku=self.instance.product_sku)
        try:
            variant.check_quantity(quantity)
        except InsufficientStock as e:
            raise forms.ValidationError(
                _('Only %(remaining)d remaining in stock.') % {
                    'remaining': e.item.get_stock_quantity()})
        return quantity

    def save(self):
        quantity = self.cleaned_data['quantity']
        self.instance.change_quantity(quantity)


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
                quantity = line.quantity
                # remove and deallocate quantity
                stock.quantity = F('quantity') - quantity
                stock.quantity_allocated = F('quantity_allocated') - quantity
                stock.save(update_fields=['quantity', 'quantity_allocated'])
        self.instance.change_status('shipped')
        statuses = [g.status for g in order.groups.all()]
        if 'shipped' in statuses and 'new' not in statuses:
            order.change_status('shipped')


ORDER_STATUS_CHOICES = (('', pgettext_lazy('Order status field value',
                                           'All')),) + Order.STATUS_CHOICES

PAYMENT_STATUS_CHOICES = (('', pgettext_lazy('Payment status field value',
                                             'All')),) + PAYMENT_STATUS_CHOICES


class OrderFilterForm(forms.Form):
    status = forms.ChoiceField(choices=ORDER_STATUS_CHOICES)


class PaymentFilterForm(forms.Form):
    status = forms.ChoiceField(choices=PAYMENT_STATUS_CHOICES)
