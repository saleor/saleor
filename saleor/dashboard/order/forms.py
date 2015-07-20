from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django_prices.forms import PriceField
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...order.models import DeliveryGroup, OrderedItem, OrderNote, Order


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

    def handle_action(self, action, user):
        amount = self.cleaned_data['amount']
        if action == 'capture' and self.payment.status == 'preauth':
            self.payment.capture(amount.gross)
        elif action == 'refund' and self.payment.status == 'confirmed':
            self.payment.refund(amount.gross)
        elif action == 'release' and self.payment.status == 'preauth':
            self.payment.release()
        else:
            raise ValueError(_('Invalid payment action'))


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
            target_group = DeliveryGroup.objects.duplicate_group(old_group)
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
        try:
            self.instance.product.check_quantity(quantity)
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
        fields = []

    def clean(self):
        if self.instance.status != 'new':
            raise forms.ValidationError(_('Cannot ship this group'),
                                        code='invalid')

    def save(self):
        order = self.instance.order
        self.instance.change_status('shipped')
        statuses = [g.status for g in order.groups.all()]
        if 'shipped' in statuses and 'new' not in statuses:
            order.change_status('shipped')


ORDER_STATUS_CHOICES = (('', pgettext_lazy('Order status field value',
                                           'All')),) + Order.STATUS_CHOICES


class OrderFilterForm(forms.Form):
    status = forms.ChoiceField(choices=ORDER_STATUS_CHOICES)
