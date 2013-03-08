from django.contrib.auth.views import (
    login as django_login_view,
    logout as django_logout,
)
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import login as auth_login, authenticate

import facebook

from .forms import LoginForm, RegisterForm, EmailForm
from .models import ExternalUserID

User = get_user_model()



def login(request):
    return django_login_view(request, authentication_form=LoginForm)


def logout(request):
    return django_logout(request, template_name='registration/logout.html')


def register(request):
    ctx = {}
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

    ctx['form'] = form
    ctx['facebook_login_url'] = facebook.auth_url(
        settings.FACEBOOK_APP_ID,
        "http://localhost:8000" + reverse('registration:oauth_callback'),
        ['email'])
    return TemplateResponse(request, 'registration/register.html', ctx)


def oauth_callback(request):
    redirect_url = "http://localhost:8000" + reverse('registration:oauth_callback')
    facebook_auth_data = facebook.get_access_token_from_code(
        request.GET['code'], redirect_url, settings.FACEBOOK_APP_ID,
        settings.FACEBOOK_SECRET)

    graph = facebook.GraphAPI(facebook_auth_data['access_token'])
    fb_user_data = graph.get_object('me')

    facebook_uid = fb_user_data.get('id')
    email = fb_user_data.get('email')

    user = authenticate(facebook_uid=facebook_uid)
    if user:
        auth_login(request, user)
        messages.success(
            request,
            "You have been successfully logged in.")
        return redirect('home')

    request.session['confirmed_email'] = email
    request.session['external_service'] = 'facebook'
    request.session['external_username'] = facebook_uid

    return redirect('registration:confirm_email')


def confirm_email(request):
    if request.method == 'GET':
        email = request.session.get('confirmed_email', '')
        form = EmailForm({'email': email})
        return TemplateResponse(request, 'registration/confirm_email.html',
                                {'form': form})

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            submitted_email = form.cleaned_data['email']
            confirmed_email = request.session.get('confirmed_email', '')
            if submitted_email == confirmed_email:
                user, _ = User.objects.get_or_create(email=submitted_email)
                ExternalUserID.objects.get_or_create(
                    user=user,
                    provider=request.session.get('external_service'),
                    username=request.session.get('external_username'))
                auth_login(request, user)
                messages.success(
                    request,
                    "You have been successfully registered and logged in.")
            else:
                messages.warning(
                    request,
                    "Supplied custom email, confirmation is sent... NOT!!!")
            return redirect('home')
        else:
            return TemplateResponse(request, 'registration/confirm_email.html',
                                    {'form': form})
