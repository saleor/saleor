from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from .models import EmailConfirmationRequest, ExternalUserData
from .utils import get_client_class_for_service

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
        EmailConfirmationRequest.objects.filter(email=email).delete()
        request = EmailConfirmationRequest.objects.create(email=email)
        path = reverse('registration:confirm_email',
                       kwargs={'token': request.token})
        context = {'confirmation_url': urlparse.urljoin(self.local_host, path)}
        msg = render_to_string('registration/email/confirm_email.txt', context)
        subject = _('Email confirmation')
        EmailMessage(subject, msg, to=[email]).send()


class EmailConfirmationForm(SetPasswordForm):

    def __init__(self, email_confirmation_request, data=None):
        self.email_confirmation_request = email_confirmation_request
        super(EmailConfirmationForm, self).__init__(
            user=None, data=data, empty_permitted=True)

    def get_authenticated_user(self):
        self.user = self.email_confirmation_request.get_or_create_user()
        self.email_confirmation_request.delete()
        if self.cleaned_data.get('new_password1'):
            self.save()
        else:
            self.user.set_unusable_password()
        return authenticate(user=self.user)


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
            user, _ = User.objects.get_or_create(email=user_info['email'])
            ExternalUserData.objects.create(
                service=self.service, username=user_info['id'], user=user)
            user = authenticate(user=user)
        return user
