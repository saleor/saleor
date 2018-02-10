from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import views as django_views, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from ..cart.utils import find_and_assign_anonymous_cart
from .emails import send_activation_mail
from .forms import LoginForm, PasswordResetForm, SignupForm

UserModel = get_user_model()


@find_and_assign_anonymous_cart()
def login(request):
    kwargs = {
        'template_name': 'account/login.html',
        'authentication_form': LoginForm}
    return django_views.LoginView.as_view(**kwargs)(request, **kwargs)


@login_required
def logout(request):
    auth.logout(request)
    messages.success(request, _('You have been successfully logged out.'))
    return redirect(settings.LOGIN_REDIRECT_URL)


def signup(request):
    form = SignupForm(request.POST or None)
    if form.is_valid():
        form.save()
        password = form.cleaned_data.get('password')
        email = form.cleaned_data.get('email')
        user = auth.authenticate(
            request=request, email=email, password=password)
        if user:
            auth.login(request, user)
        if settings.EMAIL_VERIFICATION_REQUIRED:
            send_activation_mail(user)
            msg = _('User has been created. '
                    'Check your e-mail to verify your e-mail address.')
            messages.success(request, msg)
        else:
            messages.success(request, _('User has been created'))
        redirect_url = request.POST.get('next',
                                        settings.LOGIN_REDIRECT_URL)
        return redirect(redirect_url)
    ctx = {'form': form}
    return TemplateResponse(request, 'account/signup.html', ctx)


def password_reset(request):
    kwargs = {
        'template_name': 'account/password_reset.html',
        'success_url': reverse_lazy('account_reset_password_done'),
        'form_class': PasswordResetForm}
    return django_views.PasswordResetView.as_view(**kwargs)(request, **kwargs)


class PasswordResetConfirm(django_views.PasswordResetConfirmView):
    template_name = 'account/password_reset_from_key.html'
    success_url = reverse_lazy('account_reset_password_complete')
    token = None
    uidb64 = None


def password_reset_confirm(request, uidb64=None, token=None):
    kwargs = {
        'template_name': 'account/password_reset_from_key.html',
        'success_url': reverse_lazy('account_reset_password_complete'),
        'token': token,
        'uidb64': uidb64}
    return PasswordResetConfirm.as_view(**kwargs)(request, **kwargs)

@never_cache
def resend_confirmation_email(request, uidb64=None):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel.objects.get(pk=uid)
        if user.email_verified:
            messages.error(request, _(
                'This e-mail address has already been verified.'))
        else:
            send_activation_mail(user)
            messages.success(request, _(
                'Confirmation e-mail has been resent.'))
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        messages.error(request, _(
            'Could not resend confirmation e-mail. User not found.'))
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    return redirect(reverse('account_login'))


@sensitive_post_parameters()
@never_cache
def email_confirmation(request, uidb64=None, token=None):
    assert uidb64 and token
    try:
        # urlsafe_base64_decode() decodes to bytestring on Python 3
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel.objects.get(pk=uid)
        resend_url = reverse('account_resend_confirm_email', kwargs={'uidb64': uidb64})
        resend_message = mark_safe(_('Activation failed. '
            'Click <a href="%s">here</a> to resend activation e-mail'
            % resend_url)
        )
        if user.email_verified:
            messages.error(request, _(
                'This e-mail address has already been verified.'))
        else:
            if default_token_generator.check_token(user, token):
                user.email_verified = True
                user.save()
                messages.success(request, _(
                    'E-mail verification successful. You may now login.'))
            else:
                messages.info(request, resend_message)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        messages.error(request, _(
            'E-mail verification failed. User not found.'))
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    return redirect(reverse('account_login'))


