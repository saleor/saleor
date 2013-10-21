from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.utils.translation import pgettext_lazy, ugettext

from .models import (
    EmailConfirmationRequest,
    EmailChangeRequest,
    ExternalUserData)
from .utils import get_client_class_for_service
from ..communication.mail import send_email

User = get_user_model()


class LoginForm(AuthenticationForm):

    username = forms.EmailField(label=pgettext_lazy(u"Form field", u"Email"),
                                max_length=75)

    def __init__(self, request=None, *args, **kwargs):
        super(LoginForm, self).__init__(request=request, *args, **kwargs)
        if request:
            email = request.GET.get('email')
            if email:
                self.fields['username'].initial = email


class RequestEmailConfirmationForm(forms.Form):

    email = forms.EmailField()

    template = 'registration/emails/confirm_email.txt'

    def __init__(self, local_host=None, data=None):
        self.local_host = local_host
        super(RequestEmailConfirmationForm, self).__init__(data)

    def send(self):
        email = self.cleaned_data['email']
        request = self.create_request_instance()
        confirmation_url = self.local_host + request.get_confirmation_url()
        context = {'confirmation_url': confirmation_url}
        send_email(email, self.template, context)

    def create_request_instance(self):
        email = self.cleaned_data['email']
        EmailConfirmationRequest.objects.filter(email=email).delete()
        return EmailConfirmationRequest.objects.create(
            email=self.cleaned_data['email'])


class RequestEmailChangeForm(RequestEmailConfirmationForm):

    template = 'registration/emails/change_email.txt'

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(RequestEmailChangeForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError(
                ugettext('Account with this email already exists'))
        return self.cleaned_data['email']

    def create_request_instance(self):
        EmailChangeRequest.objects.filter(user=self.user).delete()
        return EmailChangeRequest.objects.create(
            email=self.cleaned_data['email'], user=self.user)


class RegisterOrResetPasswordForm(SetPasswordForm):

    def __init__(self, email_confirmation_request, data=None):
        self.email_confirmation_request = email_confirmation_request
        super(RegisterOrResetPasswordForm, self).__init__(
            user=None, data=data, empty_permitted=True)

    def get_authenticated_user(self):
        self.user = self.email_confirmation_request.get_or_create_user()
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
