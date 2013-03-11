from django.contrib.auth.views import (
    login as django_login_view,
    logout as django_logout,
)
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import login as auth_login, authenticate
from django.http import HttpResponseNotFound

import facebook
import httplib2
import json

from .forms import LoginForm, RegisterForm, EmailForm
from .models import ExternalUserID
from .utils import callback_url, get_google_flow, google_query_url

User = get_user_model()


def login(request):
    ctx = {
        'facebook_login_url': facebook.auth_url(
            settings.FACEBOOK_APP_ID,
            callback_url('facebook'),
            ['email']),
        'google_login_url':
        'https://accounts.google.com/o/oauth2/auth?'
        'scope=https://www.googleapis.com/auth/userinfo.email+'
        'https://www.googleapis.com/auth/plus.me&'
        'redirect_uri=http://localhost:8000/account/oauth_callback/google/'
        '&response_type=code&client_id=656911639082.apps.googleusercontent.com'
    }
    return django_login_view(request, authentication_form=LoginForm,
                             extra_context=ctx)


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
    return TemplateResponse(request, 'registration/register.html', ctx)


def oauth_callback(request, service):
    email = None
    external_username = None

    if service == 'facebook':
        facebook_auth_data = facebook.get_access_token_from_code(
            request.GET['code'], callback_url('facebook'),
            settings.FACEBOOK_APP_ID, settings.FACEBOOK_SECRET)

        graph = facebook.GraphAPI(facebook_auth_data['access_token'])
        fb_user_data = graph.get_object('me')

        external_username = fb_user_data.get('id')
        email = fb_user_data.get('email')

        user = authenticate(external_service='facebook',
                            external_username=external_username)
    elif service == 'google':
        code = request.GET['code']
        credentials = get_google_flow().step2_exchange(code)
        http = credentials.authorize(httplib2.Http())
        _header, content = http.request(google_query_url())
        google_user_data = json.loads(content)
        email = (google_user_data['email']
                 if google_user_data.get('verified_email')
                 else '')
        external_username = google_user_data['id']
        user = authenticate(external_service='google',
                            external_username=external_username)

    else:
        return HttpResponseNotFound()

    if user:
        auth_login(request, user)
        messages.success(
            request,
            "You have been successfully logged in.")
        return redirect('home')

    request.session['confirmed_email'] = email
    request.session['external_service'] = service
    request.session['external_username'] = external_username

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
                external_username = request.session.get('external_username')
                external_service = request.session.get('external_service')
                user, _ = User.objects.get_or_create(email=submitted_email)
                ExternalUserID.objects.get_or_create(
                    user=user,
                    provider=external_service,
                    username=external_username)
                user = authenticate(user=user)
                auth_login(request, user)
                messages.success(
                    request,
                    "You have been successfully registered and logged in.")
            else:
                messages.warning(
                    request,
                    "Supplied custom email, confirmation is sent... NOT!!! "
                    "Actually this is a TODO, to sent activation email now")
            return redirect('home')
        else:
            return TemplateResponse(request, 'registration/confirm_email.html',
                                    {'form': form})
