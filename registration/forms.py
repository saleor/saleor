from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

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
