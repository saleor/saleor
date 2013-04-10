from django.contrib.auth.views import (
    login as django_login_view,
    logout as django_logout,
)
from django.contrib import messages
from django.contrib.auth import (
    login as auth_login,
    authenticate,
    get_user_model,
)
from django.core.urlresolvers import reverse
from django.core.mail.message import EmailMessage
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone

from .forms import LoginForm, EmailForm, EmailConfirmationFormset
from .models import ExternalUserData, EmailConfirmation
from .utils import (
    facebook_callback,
    google_callback,
    get_google_login_url,
    get_facebook_login_url,
    get_email_confirmation_message,
    get_protocol_and_host,
)

User = get_user_model()
now = timezone.now


def login(request):
    local_host = get_protocol_and_host(request)
    ctx = {'facebook_login_url': get_facebook_login_url(local_host),
           'google_login_url': get_google_login_url(local_host)}
    return django_login_view(request, authentication_form=LoginForm,
                             extra_context=ctx)


def logout(request):
    return django_logout(request, template_name='registration/logout.html')


def oauth_callback(request, service):
    local_host = get_protocol_and_host(request)

    if service == 'facebook':
        email, external_username = facebook_callback(local_host, request.GET)
    elif service == 'google':
        email, external_username = google_callback(local_host, request.GET)
    else:
        return HttpResponseNotFound()

    if not external_username:
        messages.warning(
            request,
            'Failed to retrieve user information from external service. '
            'Please try again.')
        return redirect(reverse('registration:login'))

    user = authenticate(external_service=service,
                        external_username=external_username)

    if user:
        _login_user(request, user)
        return redirect('home')
    else:
        request.session['confirmed_email'] = email
        request.session['external_service'] = service
        request.session['external_username'] = external_username
        return redirect('registration:register')


def register(request):
    local_host = get_protocol_and_host(request)

    if request.method == 'GET':
        email = request.session.get('confirmed_email', None)
        form = EmailForm({'email': email} if email else None)

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            submitted_email = form.cleaned_data['email']
            confirmed_email = request.session.pop('confirmed_email', '')
            try:
                external_user_data = {
                    'username': request.session.pop('external_username'),
                    'provider': request.session.pop('external_service')
                }
            except KeyError:
                external_user = None
            else:
                external_user, _ = ExternalUserData.objects.get_or_create(
                    **external_user_data)

            if submitted_email == confirmed_email:
                if not external_user:
                    # TODO: this should never happen unless sb is hacking
                    return HttpResponseBadRequest()
                user, _ = User.objects.get_or_create(email=submitted_email)
                if external_user and not external_user.user:
                    external_user.user = user
                    external_user.save()
                user = authenticate(user=user)
                _login_user(request, user)
            else:
                email_confirmation = EmailConfirmation.objects.create(
                    email=submitted_email, external_user=external_user)
                message = get_email_confirmation_message(
                    local_host, email_confirmation)
                subject = '[Saleor] Email confirmation'
                EmailMessage(subject, message, to=[submitted_email]).send()
                messages.warning(
                    request,
                    'We have sent you a confirmation email. '
                    'Please check your inbox.')
            return redirect('home')

    return TemplateResponse(request, 'registration/register.html',
                            {'form': form})


def confirm_email(request, pk, token):
    try:
        email_confirmation = EmailConfirmation.objects.get(
            pk=pk, token=token, valid_until__gte=now())
        # TODO: cronjob (celery task) to delete stale tokens
    except EmailConfirmation.DoesNotExist:
        return TemplateResponse(request, 'registration/invalid_token.html')

    if request.method == 'GET':
        formset = EmailConfirmationFormset(
            email_confirmation=email_confirmation)

    if request.method == 'POST':
        formset = EmailConfirmationFormset(
            email_confirmation=email_confirmation, data=request.POST)
        if formset.is_valid():
            user = formset.save()
            user = authenticate(user=user)
            _login_user(request, user)
            return redirect('home')

    return TemplateResponse(
        request, 'registration/set_password.html', {'formset': formset})


def _login_user(request, user):
    auth_login(request, user)
    msg = 'You have been successfully logged in.'
    messages.success(request, msg)
