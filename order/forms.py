from django import forms
from userprofile.forms import AddressForm


class ShippingForm(AddressForm):

    use_billing = forms.BooleanField(initial=True)


class ManagementForm(forms.Form):

    CHOICES = (
        ('select', 'Select address'),
        ('new', 'Add new address')
    )

    choice_method = forms.ChoiceField(choices=CHOICES)
