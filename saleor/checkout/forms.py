from django import forms
from django.utils.translation import ugettext_lazy as _


class AddressChoiceIterator(forms.models.ModelChoiceIterator):

    def __iter__(self):
        first_choice = self.field.first_choice
        if first_choice:
            yield first_choice
        for obj in self.queryset:
            yield self.choice(obj)
        yield self.field.last_choice


class AddressChoiceField(forms.ModelChoiceField):
    first_choice = 'copy', _('Use shipping address')
    last_choice = 'new', _('Enter a new address')

    def __init__(self, can_copy, *args, **kwargs):
        if not can_copy:
            self.first_choice = None
        super(AddressChoiceField, self).__init__(*args, **kwargs)

    def validate(self, value):
        if not self.if_special_choice(value):
            return super(AddressChoiceField, self).validate(value)

    def to_python(self, value):
        if self.is_special_choice(value):
            return value
        else:
            return super(AddressChoiceField, self).to_python(value)

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return AddressChoiceIterator(self)

    choices = property(_get_choices, forms.ChoiceField._set_choices)

    def if_special_choice(self, value):
        return value == self.last_choice[0] or (
            self.first_choice and value == self.first_choice[0])


class UserAddressesForm(forms.Form):
    def __init__(self, queryset, can_copy=False, *args, **kwargs):
        super(UserAddressesForm, self).__init__(*args, **kwargs)
        self.fields['address'] = AddressChoiceField(queryset=queryset,
                                                    widget=forms.RadioSelect,
                                                    can_copy=can_copy)


class DeliveryForm(forms.Form):
    method = forms.ChoiceField(label=_('Shipping method'),
                               widget=forms.RadioSelect)

    def __init__(self, delivery_choices, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        method_field = self.fields['method']
        method_field.choices = delivery_choices
        if len(delivery_choices) == 1:
            method_field.initial = delivery_choices[0][1]


class AnonymousEmailForm(forms.Form):
    email = forms.EmailField()
