from django.contrib.auth.views import (
    login as django_login,
    logout as django_logout,
)
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.contrib import messages
from django.shortcuts import redirect

from .forms import LoginForm, RegisterForm

User = get_user_model()


def login(request):
    return django_login(request, authentication_form=LoginForm)


def logout(request):
    return django_logout(request, template_name='registration/logout.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            User.objects.create_user(
                form.cleaned_data['email'], form.cleaned_data['password'])
            messages.success(
                request,
                "You have been successfully registered. You may login now.")
            return redirect("registration:login")
    else:
        form = RegisterForm()
    return TemplateResponse(request, 'registration/register.html',
                            {'form': form})
