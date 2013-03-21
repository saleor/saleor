from .models import DigitalDeliveryGroup
from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
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
        self.is_user_authenticated = is_user_authenticated
        if not is_user_authenticated:
            choice_method = self.fields['choice_method']
            choice_method.initial = self.CHOICES[1][0]
            choice_method.widget = choice_method.hidden_widget()

    def clean(self):
        cleaned_data = super(ManagementForm, self).clean()
        choice_method = cleaned_data.get('choice_method')
        if choice_method == 'select' and not self.is_user_authenticated:
            raise forms.ValidationError('Only authenticated users can select '
                                        'address.')
        return cleaned_data


class DigitalDeliveryForm(forms.ModelForm):

    class Meta:
        model = DigitalDeliveryGroup
        exclude = ['order', 'price']

    def __init__(self, *args, **kwargs):
        super(DigitalDeliveryForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True


class DeliveryField(forms.ChoiceField):

    def __init__(self, methods, *args, **kwargs):
        self.methods = list(methods)
        choices = [(index, unicode(method)) for index, method in
                   enumerate(self.methods)]
        super(DeliveryField, self).__init__(choices, *args, **kwargs)

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        try:
            return self.methods[int(value)]
        except (IndexError, ValueError):
            raise ValidationError(
                self.error_messages['invalid_choice'] % {'value':value})

    def valid_value(self, value):
        return value in self.methods


class DeliveryForm(forms.Form):

    def __init__(self, group, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        self.fields['method'] = DeliveryField(group.get_delivery_methods())
