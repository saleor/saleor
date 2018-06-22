from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import CustomerNote, User


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
        can_edit_staff_users = self.user.has_perm('account.edit_staff')
        if not can_edit_staff_users:
            raise forms.ValidationError(pgettext_lazy(
                'Edit customer details in order form error',
                'You have insufficient permissions, to edit staff users.'))
        return data


class CustomerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # disable 'is_active' checkbox if user edits his own account
        if self.user == self.instance:
            self.fields['is_active'].disabled = True
            self.fields['note'].disabled = True

    class Meta:
        model = User
        fields = ['email', 'is_active', 'note']


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
