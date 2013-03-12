from django.contrib.auth.views import (
    login as django_login_view,
    logout as django_logout,
)
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login as auth_login, authenticate
from django.http import HttpResponseNotFound
from django.core.urlresolvers import reverse

from .forms import LoginForm, RegisterForm, EmailForm
from .models import ExternalUserID
from .utils import (
    facebook_callback,
    google_callback,
    get_google_login_url,
    get_facebook_login_url,
)

User = get_user_model()


def login(request):
    ctx = {
        'facebook_login_url': get_facebook_login_url(),
        'google_login_url': get_google_login_url()
    }
    return django_login_view(request, authentication_form=LoginForm,
                             extra_context=ctx)


def logout(request):
    return django_logout(request, template_name='registration/logout.html')


def register(request):  # pragma: no cover
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

    ctx = {'form': form}
    return TemplateResponse(request, 'registration/register.html', ctx)


def oauth_callback(request, service):
    if service == 'facebook':
        email, external_username = facebook_callback(request.GET)
    elif service == 'google':
        email, external_username = google_callback(request.GET)
    else:
        return HttpResponseNotFound()

    if not external_username:
        messages.warning(
            request,
            "Failed to retrieve user information from external service."
            " Please try again.")
        return redirect(reverse('registration:login'))

    user = authenticate(external_service=service,
                        external_username=external_username)

    if user:
        auth_login(request, user)
        messages.success(
            request,
            "You have been successfully logged in.")
        return redirect('home')
    else:
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
