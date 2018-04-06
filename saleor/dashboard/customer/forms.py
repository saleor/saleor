from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import CustomerNote, User


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
