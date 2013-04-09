from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm

User = get_user_model()


class LoginForm(AuthenticationForm):

    username = forms.EmailField(label=_("Email"), max_length=75)


class EmailForm(forms.Form):

    email = forms.EmailField()


class RegisterForm(EmailForm):

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('Email already registered.')
        return email


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

    def save(self):
        user = self.email_confirmation.get_or_create_user()
        self.email_confirmation.delete()
        if not self.no_password():
            self.set_password_form.user = user
            user = self.set_password_form.save()
        return user
