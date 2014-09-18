from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import BaseFormSet, DEFAULT_MAX_NUM
from satchless.item import InsufficientStock

from ...cart.forms import QuantityField
from ...order.models import OrderNote
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


class OrderLineForm(forms.Form):
    quantity = QuantityField()

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        super(OrderLineForm, self).__init__(*args, **kwargs)

    def get_variant(self):
        p = Product.objects.select_subclasses().get(pk=self.item.product.pk)
        return p.variants.get(name=self.item.product_name)

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
        if new_quantity != self.item.quantity and new_quantity > 0:
            self.item.change_quantity(new_quantity, user)


class OrderContentFormset(BaseFormSet):
    absolute_max = 9999
    can_delete = False
    can_order = False
    extra = 0
    form = OrderLineForm
    max_num = DEFAULT_MAX_NUM
    validate_max = False
    min_num = None
    validate_min = False

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        kwargs['initial'] = [{'quantity': item.quantity}
                             for item in self.order.get_items()]
        super(OrderContentFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['item'] = self.order.get_items()[i]
        return super(OrderContentFormset, self)._construct_form(i, **kwargs)

    def save(self, user=None):
        for form in self.forms:
            if form.is_valid():
                form.save(user)
