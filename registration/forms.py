from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginForm(AuthenticationForm):

    username = forms.EmailField(label=_("Email"), max_length=75)


class RegisterForm(forms.Form):

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('Email already registered')
        return self.cleaned_data


class EmailForm(forms.Form):

    email = forms.EmailField()
