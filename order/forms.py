from django import forms
from userprofile.forms import AddressForm

class ShippingForm(AddressForm):

    use_billing = forms.BooleanField(initial=True)


class ManagementForm(forms.Form):

    CHOICES = (
        ('select', 'Select address'),
        ('new', 'Complete address')
    )

    choice_method = forms.ChoiceField(choices=CHOICES, initial=CHOICES[0][0])

    def __init__(self, is_user_authenticated, *args, **kwargs):
        super(ManagementForm, self).__init__(*args, **kwargs)
        if not is_user_authenticated:
            choice_method = self.fields['choice_method']
            choice_method.initial = self.CHOICES[1][0]
            choice_method.widget = choice_method.hidden_widget()


