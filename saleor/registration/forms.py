from __future__ import unicode_literals

import emailit.api
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.utils.translation import pgettext_lazy, ugettext

User = get_user_model()

from .models import (
    EmailConfirmationRequest,
    EmailChangeRequest,
    ExternalUserData)
from .utils import get_client_class_for_service


class LoginForm(AuthenticationForm):

    username = forms.EmailField(label=pgettext_lazy('Form field', 'Email'),
                                max_length=75)

    def __init__(self, request=None, *args, **kwargs):
        super(LoginForm, self).__init__(request=request, *args, **kwargs)
        if request:
            email = request.GET.get('email')
            if email:
                self.fields['username'].initial = email


class SetOrRemovePasswordForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):
        super(SetOrRemovePasswordForm, self).__init__(*args, **kwargs)
        if not 'new_password1' in self.data.keys():
            self.fields['new_password1'].required = False
            self.fields['new_password2'].required = False

    def save(self, commit=True):
        if self.cleaned_data.get('new_password1'):
            return super(SetOrRemovePasswordForm, self).save(commit)
        else:
            self.user.set_unusable_password()
        return self.user


class RequestEmailConfirmationForm(forms.Form):

    email = forms.EmailField()

    template = 'registration/emails/confirm_email'

    def __init__(self, local_host=None, data=None):
        self.local_host = local_host
        super(RequestEmailConfirmationForm, self).__init__(data)

    def send(self):
        email = self.cleaned_data['email']
        request = self.create_request_instance()
        confirmation_url = self.local_host + request.get_confirmation_url()
        context = {'confirmation_url': confirmation_url}
        emailit.api.send_mail([email], context, self.template)

    def create_request_instance(self):
        email = self.cleaned_data['email']
        EmailConfirmationRequest.objects.filter(email=email).delete()
        return EmailConfirmationRequest.objects.create(
            email=self.cleaned_data['email'])


class RequestEmailChangeForm(RequestEmailConfirmationForm):

    template = 'registration/emails/change_email'

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(RequestEmailChangeForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                ugettext('Account with this email already exists'))
        return self.cleaned_data['email']

    def create_request_instance(self):
        EmailChangeRequest.objects.filter(user=self.user).delete()
        return EmailChangeRequest.objects.create(
            email=self.cleaned_data['email'], user=self.user)


class OAuth2CallbackForm(forms.Form):

    code = forms.CharField()
    error_code = forms.CharField(required=False)
    error_message = forms.CharField(required=False)

    def __init__(self, service, local_host, data):
        self.service = service
        self.local_host = local_host
        super(OAuth2CallbackForm, self).__init__(data)

    def clean_error_message(self):
        error_message = self.cleaned_data.get('error_message')
        if error_message:
            raise forms.ValidationError(error_message)

    def get_authenticated_user(self):
        code = self.cleaned_data.get('code')
        client_class = get_client_class_for_service(self.service)
        client = client_class(local_host=self.local_host, code=code)
        user_info = client.get_user_info()
        user = authenticate(service=self.service, username=user_info['id'])
        if not user:
            user, _ = User.objects.get_or_create(
                email=user_info['email'])
            ExternalUserData.objects.create(
                service=self.service, username=user_info['id'], user=user)
            user = authenticate(user=user)
        return user
