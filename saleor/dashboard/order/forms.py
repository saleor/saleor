from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...order.models import DeliveryGroup, OrderedItem, OrderNote
from ...product.models import Product


class OrderNoteForm(forms.ModelForm):

    class Meta:
        model = OrderNote
        fields = ['content']
        widgets = {'content': forms.Textarea({
            'rows': 5, 'placeholder': _('Note')})}

    def __init__(self, *args, **kwargs):
        super(OrderNoteForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''


class ManagePaymentForm(forms.Form):
    amount = forms.DecimalField(min_value=0, decimal_places=2, required=False)

    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment')
        super(ManagePaymentForm, self).__init__(*args, **kwargs)

    def handle_action(self, action, user):
        amount = self.cleaned_data['amount']
        if action == 'capture' and self.payment.status == 'preauth':
            self.payment.capture(amount)
        elif action == 'refund' and self.payment.status == 'confirmed':
            self.payment.refund(amount)
        elif action == 'release' and self.payment.status == 'preauth':
            self.payment.release()
        else:
            raise ValueError(_('Invalid payment action'))


class MoveItemsForm(forms.Form):
    how_many = QuantityField()
    groups = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        super(MoveItemsForm, self).__init__(*args, **kwargs)
        self.fields['how_many'].widget.attrs.update({
            'max': self.item.quantity,
            'min': 1})
        self.fields['groups'].choices = self.get_delivery_group_choices()

    def get_delivery_group_choices(self):
        group = self.item.delivery_group
        groups = group.order.groups.exclude(pk=group.pk).exclude(
            status='cancelled')
        choices = [('new', _('New'))]
        choices.extend([(g.pk, str(g)) for g in groups])
        return choices

    def move_items(self):
        how_many = self.cleaned_data['how_many']
        choice = self.cleaned_data['groups']
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
        self.fields['quantity'].widget.attrs.update({
            'max': self.instance.quantity,
            'min': 1})
        self.fields['quantity'].initial = self.initial_quantity

    def get_variant(self):
        p = Product.objects.select_subclasses().get(pk=self.instance.product.pk)
        return p.variants.get(sku=self.instance.product_sku)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        variant = self.get_variant()
        try:
            variant.check_quantity(quantity)
        except InsufficientStock as e:
            msg = _('Only %(remaining)d remaining in stock.')
            raise forms.ValidationError(msg % {'remaining': e.item.stock})
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
