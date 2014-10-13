from django import forms
from django.utils.translation import ugettext_lazy as _
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...order.models import OrderNote, DeliveryGroup
from ...product.models import Product


class OrderNoteForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OrderNoteForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''

    class Meta:
        model = OrderNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea({'rows': 5, 'placeholder': _('Note')})
        }


class ManagePaymentForm(forms.Form):
    amount = forms.DecimalField(min_value=0, decimal_places=2)


class MoveItemsForm(forms.Form):
    quantity = QuantityField()
    groups = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        super(MoveItemsForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['max'] = self.item.quantity
        self.fields['groups'].choices = self.get_delivery_group_choices()

    def get_delivery_group_choices(self):
        group = self.item.delivery_group
        groups = group.order.groups.exclude(pk=group.pk)
        choices = [('new', _('New'))]
        choices.extend([(g.pk, 'Delivery group #%s' % g.pk) for g in groups])
        return choices

    def save(self, user=None):
        quantity = self.cleaned_data['quantity']
        choice = self.cleaned_data['groups']
        if choice == 'new':
            group = DeliveryGroup.objects.select_subclasses().get(
                pk=self.item.delivery_group.pk)
            new_group = group
            new_group.pk = None
            new_group.id = None
            new_group.status = 'new'

            address = group.address
            address.pk = None
            address.save()
            new_group.address = address

            new_group.save()
            self.item.move_to_group(new_group, quantity, user)
        else:
            group = DeliveryGroup.objects.get(pk=choice)
            self.item.move_to_group(group, quantity, user)


class ChangeQuantityForm(forms.Form):
    quantity = QuantityField()

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        super(ChangeQuantityForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['max'] = self.item.quantity
        self.fields['quantity'].initial = self.item.quantity

    def get_variant(self):
        p = Product.objects.select_subclasses().get(pk=self.item.product.pk)
        return p.variants.get(sku=self.item.product_sku)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        variant = self.get_variant()
        try:
            variant.check_quantity(quantity)
        except InsufficientStock as e:
            msg = _('Only %(remaining)d remaining in stock.')
            raise forms.ValidationError(msg % {'remaining': e.item.stock})
        return quantity

    def save(self, user=None):
        new_quantity = self.cleaned_data['quantity']
        if new_quantity != self.item.quantity:
            self.item.change_quantity(new_quantity, user)
