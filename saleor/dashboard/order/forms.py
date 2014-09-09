from django import forms
from django.utils.translation import ugettext_lazy as _

from ...order.models import OrderNote


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
