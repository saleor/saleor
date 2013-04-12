from django.contrib.auth.views import (
    login as django_login_view,
    logout as django_logout_view)
from django.contrib import messages
from django.contrib.auth import (
    login as auth_login,
    get_user_model)
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .forms import (
    EmailConfirmationFormset,
    RequestEmailConfirmationForm,
    LoginForm,
    OAuth2CallbackForm)
from .models import EmailConfirmation
from .utils import (
    get_facebook_login_url,
    get_google_login_url,
    get_protocol_and_host)

User = get_user_model()
now = timezone.now


def login(request):
    local_host = get_protocol_and_host(request)
    ctx = {'facebook_login_url': get_facebook_login_url(local_host),
           'google_login_url': get_google_login_url(local_host)}
    return django_login_view(request, authentication_form=LoginForm,
                             extra_context=ctx)


def logout(request):
    return django_logout_view(request, template_name='registration/logout.html')


def oauth_callback(request, service):
    local_host = get_protocol_and_host(request)
    form = OAuth2CallbackForm(service=service, local_host=local_host,
                              data=request.GET)
    if form.is_valid():
        try:
            user = form.get_authenticated_user()
            _login_user(request, user)
            return redirect('home')
        except ValueError, e:
            messages.warning(request, unicode(e))
    else:
        for field, errors in form.errors.items():
            print form.errors
            for error in errors:
                messages.warning(request, '[%s] %s' % (field, error))
    return redirect('registration:login')


def request_email_confirmation(request):
    local_host = get_protocol_and_host(request)
    if request.method == 'POST':
        form = RequestEmailConfirmationForm(local_host=local_host,
                                            data=request.POST)
        if form.is_valid():
            form.send()
            msg = _('Confirmation email has been sent. '
                    'Please check your inbox.')
            messages.success(request, msg)
            return redirect('home')
    else:
        form = RequestEmailConfirmationForm(local_host=local_host)

    return TemplateResponse(request,
                            'registration/request_email_confirmation.html',
                            {'form': form})


def confirm_email(request, pk, token):
    try:
        email_confirmation = EmailConfirmation.objects.get(
            pk=pk, token=token, valid_until__gte=now())
        # TODO: cronjob (celery task) to delete stale tokens
    except EmailConfirmation.DoesNotExist:
        return TemplateResponse(request, 'registration/invalid_token.html')

    if request.method == 'POST':
        formset = EmailConfirmationFormset(
            email_confirmation=email_confirmation, data=request.POST)
        if formset.is_valid():
            user = formset.get_authenticated_user()
            _login_user(request, user)
            return redirect('home')
    else:
        formset = EmailConfirmationFormset(
            email_confirmation=email_confirmation)

    return TemplateResponse(
        request, 'registration/set_password.html', {'formset': formset})


def _login_user(request, user):
    auth_login(request, user)
    msg = _('You have been successfully logged in.')
    messages.success(request, msg)
