from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import CustomerNote, User


def get_name_placeholder(name):
    return pgettext_lazy(
        'Customer form: Name field placeholder',
        '%(name)s (Inherit from default billing address)') % {
            'name': name}


class CustomerDeleteForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if not self.instance.is_staff:
            return data

        if self.instance == self.user:
            raise forms.ValidationError(pgettext_lazy(
                'Edit customer details in order form error',
                'You can\'t delete your own account via dashboard, '
                'please try from the storefront.'))
        if self.instance.is_superuser:
            raise forms.ValidationError(pgettext_lazy(
                'Edit customer details in order form error',
                'Only superuser can delete his own account.'))
        can_manage_staff_users = self.user.has_perm('account.manage_staff')
        if not can_manage_staff_users:
            raise forms.ValidationError(pgettext_lazy(
                'Edit customer details in order form error',
                'You have insufficient permissions, to edit staff users.'))
        return data


class CustomerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # The user argument is required
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Disable editing following fields if user edits his own account
        if self.user == self.instance:
            self.fields['note'].disabled = True
            self.fields['is_active'].disabled = True

        address = self.instance.default_billing_address
        if not address:
            return
        if address.first_name:
            placeholder = get_name_placeholder(address.first_name)
            self.fields['first_name'].widget.attrs['placeholder'] = placeholder
        if address.last_name:
            placeholder = get_name_placeholder(address.last_name)
            self.fields['last_name'].widget.attrs['placeholder'] = placeholder

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'note', 'is_active']
        labels = {
            'first_name': pgettext_lazy(
                'Customer form: Given name field', 'Given name'),
            'last_name': pgettext_lazy(
                'Customer form: Family name field', 'Family name'),
            'email': pgettext_lazy(
                'Customer form: email address field', 'Email'),
            'note': pgettext_lazy(
                'Customer form: customer note field', 'Notes'),
            'is_active': pgettext_lazy(
                'Customer form: is active toggle', 'User is active')}


class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = CustomerNote
        fields = ['content', 'is_public']
        widget = {
            'content': forms.Textarea()}
        labels = {
            'content': pgettext_lazy('Customer note', 'Note'),
            'is_public': pgettext_lazy(
                'Allow customers to see note toggle',
                'Customer can see this note')}
