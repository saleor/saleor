from django.conf import settings
from django.contrib.auth import forms as django_forms, update_session_auth_hash
from phonenumbers.phonenumberutil import country_code_for_region

from .i18n import AddressMetaForm, get_address_form_class


def get_address_form(
        data, country_code, initial=None, instance=None, **kwargs):
    country_form = AddressMetaForm(data, initial=initial)
    preview = False
    if country_form.is_valid():
        country_code = country_form.cleaned_data['country']
        preview = country_form.cleaned_data['preview']

    if initial is None and country_code:
        initial = {}
    if country_code:
        initial['phone'] = '+{}'.format(country_code_for_region(country_code))

    address_form_class = get_address_form_class(country_code)

    if not preview and instance is not None:
        address_form_class = get_address_form_class(
            instance.country.code)
        address_form = address_form_class(
            data, instance=instance, **kwargs)
    else:
        initial_address = (
            initial if not preview
            else data.dict() if data is not None else data)
        address_form = address_form_class(
            not preview and data or None,
            initial=initial_address,
            **kwargs)
    return address_form, preview


class ChangePasswordForm(django_forms.PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].user = self.user
        self.fields['old_password'].widget.attrs['placeholder'] = ''
        self.fields['new_password1'].widget.attrs['placeholder'] = ''
        del self.fields['new_password2']


def logout_on_password_change(request, user):
    if (update_session_auth_hash is not None and
            not settings.LOGOUT_ON_PASSWORD_CHANGE):
        update_session_auth_hash(request, user)
