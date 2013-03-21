from datetime import datetime

from django.contrib.auth.views import (
    login as django_login_view, logout as django_logout,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.template.response import TemplateResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login as auth_login, authenticate
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.core.mail.message import EmailMessage

from .forms import LoginForm, EmailForm
from .models import ExternalUserData, EmailConfirmation
from .utils import (
    facebook_callback,
    google_callback,
    get_google_login_url,
    get_facebook_login_url,
    get_email_confirmation_message,
)

User = get_user_model()
now = datetime.now


def login(request):
    ctx = {
        'facebook_login_url': get_facebook_login_url(),
        'google_login_url': get_google_login_url()
    }
    return django_login_view(request, authentication_form=LoginForm,
                             extra_context=ctx)


def logout(request):
    return django_logout(request, template_name='registration/logout.html')


def register(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            email_confirmation = EmailConfirmation.objects.create(
                email=email)
            message = get_email_confirmation_message(
                request, email_confirmation)
            subject = "[Saleor] Email confirmation"
            EmailMessage(subject, message, to=[email]).send()
            messages.warning(
                request,
                "We have sent you a verifiacation email. "
                "Please check your email inbox.")
            return redirect("home")
    else:
        form = EmailForm()

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

        return redirect('registration:select_email')


def select_email(request):
    if request.method == 'GET':
        email = request.session.get('confirmed_email', '')
        form = EmailForm({'email': email})
        return TemplateResponse(request, 'registration/select_email.html',
                                {'form': form})

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            submitted_email = form.cleaned_data['email']
            confirmed_email = request.session.pop('confirmed_email', '')
            try:
                external_username = request.session.pop('external_username')
                external_service = request.session.pop('external_service')
            except KeyError:
                return HttpResponseBadRequest()
            if submitted_email == confirmed_email:
                user, _ = User.objects.get_or_create(email=submitted_email)
                external_user_data, _ = ExternalUserData.objects.get_or_create(
                    provider=external_service,
                    username=external_username)
                if not external_user_data.user:
                    external_user_data.user = user
                    external_user_data.save()
                user = authenticate(user=user)
                auth_login(request, user)
                messages.success(
                    request,
                    "You have been successfully logged in.")
            else:
                external_user, _ = ExternalUserData.objects.get_or_create(
                    provider=external_service, username=external_username)
                email_confirmation = EmailConfirmation.objects.create(
                    email=submitted_email, external_user=external_user)
                message = get_email_confirmation_message(
                    request, email_confirmation)
                subject = "[Saleor] Email confirmation"
                EmailMessage(subject, message, to=[submitted_email]).send()
                messages.warning(
                    request,
                    "Supplied custom email, confirmation sent. "
                    "Please check your email.")
            return redirect('home')
        else:
            return TemplateResponse(request, 'registration/select_email.html',
                                    {'form': form})


def confirm_email(request, pk, token):
    try:
        email_confirmation = EmailConfirmation.objects.get(
            pk=pk, token=token, valid_until__gte=now())
        # TODO: cronjob (celery task) to delete stale tokens
    except EmailConfirmation.DoesNotExist:
        return TemplateResponse(request, 'registration/invalid_token.html')

    proceed = False
    password = None

    if request.method == 'GET':
        form = SetPasswordForm(user=None)
    elif request.method == 'POST':
        if "nopassword" in request.POST:
            proceed = True
        else:
            form = SetPasswordForm(user=None, data=request.POST)
            if form.is_valid():
                proceed = True
                password = form.cleaned_data['new_password1']

    if proceed:
        user = email_confirmation.get_confirmed_user()
        if password:
            user.set_password(password)
            user.save()
        email_confirmation.delete()

        user = authenticate(user=user)
        auth_login(request, user)
        messages.success(
            request,
            "You have been successfully registered and logged in.")
        return redirect('home')
    else:
        return TemplateResponse(
            request, "registration/set_password.html", {"form": form})
