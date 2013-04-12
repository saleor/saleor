from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from .models import EmailConfirmation, ExternalUserData
from .utils import get_client_class_for_serivce

import urlparse

User = get_user_model()


class LoginForm(AuthenticationForm):

    username = forms.EmailField(label=_("Email"), max_length=75)


class RequestEmailConfirmationForm(forms.Form):

    email = forms.EmailField()

    def __init__(self, local_host, data=None):
        self.local_host = local_host
        super(RequestEmailConfirmationForm, self).__init__(data)

    def send(self):
        email = self.cleaned_data['email']
        request = EmailConfirmation.objects.create(email=email)
        path = reverse('registration:confirm_email',
                       kwargs={'pk': request.pk,
                               'token': request.token})
        context = {'confirmation_url': urlparse.urljoin(self.local_host, path)}
        msg = render_to_string('registration/email/confirm_email.txt', context)
        subject = _('Email confirmation')
        EmailMessage(subject, msg, to=[email]).send()


class NoPasswordForm(forms.Form):

    no_password = forms.BooleanField(initial=True, widget=forms.HiddenInput())


class EmailConfirmationFormset(object):

    def __init__(self, email_confirmation, data=None):
        self.email_confirmation = email_confirmation
        self.set_password_form = SetPasswordForm(user=False, data=data)
        self.no_password_form = NoPasswordForm(data=data)

    def no_password(self):
        return self.no_password_form.cleaned_data.get('no_password')

    def is_valid(self):
        if self.no_password_form.is_valid() and self.no_password():
            return True
        else:
            return self.set_password_form.is_valid()

    def get_authenticated_user(self):
        user = self.email_confirmation.get_or_create_user()
        self.email_confirmation.delete()
        if not self.no_password():
            self.set_password_form.user = user
            user = self.set_password_form.save()
        user = authenticate(user=user)
        return user


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
        client_class = get_client_class_for_serivce(self.service)
        client = client_class(local_host=self.local_host, code=code)
        user_info = client.get_user_info()
        user = authenticate(external_service=self.service,
                            external_username=user_info['id'])
        if not user:
            user, _ = User.objects.get_or_create(email=user_info['email'])
            external_user, _ = ExternalUserData.objects.get_or_create(
                username=user_info['id'], provider=self.service, user=user)
            user = authenticate(user=user)
        return user
