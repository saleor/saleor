from django import forms
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import pgettext

from ..models import User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=pgettext('Form field', 'Email'), max_length=75)

    def __init__(self, request=None, *args, **kwargs):
        super(LoginForm, self).__init__(request=request, *args, **kwargs)
        if request:
            email = request.GET.get('email')
            if email:
                self.fields['username'].initial = email


class SignupForm(forms.ModelForm):
    password = forms.CharField(
        label=pgettext('User form field', 'Password'), strip=False,
        widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        if self._meta.model.USERNAME_FIELD in self.fields:
            self.fields[self._meta.model.USERNAME_FIELD].widget.attrs.update(
                {'autofocus': ''})

    def save(self, request=None, commit=True):
        user = super(SignupForm, self).save(commit=False)
        password = self.cleaned_data['password']
        user.set_password(password)
        if commit:
            user.save()
            if request:
                login(request, user)
        return user
