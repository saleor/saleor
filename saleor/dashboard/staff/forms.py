from django.contrib.auth.models import Permission
from django import forms


class PermissionsForm(forms.Form):
    permission_options = (
        ('view', 'View'),
        ('edit', 'Edit'),
    )
    product = forms.MultipleChoiceField(label='Product',
                                        required=False,
                                        choices=permission_options,
                                        widget=forms.CheckboxSelectMultiple)
    # categories = forms.MultipleChoiceField(label='Categories',
    #                                        required=False,
    #                                        choices=permission_options,
    #                                        widget=forms.CheckboxSelectMultiple)

