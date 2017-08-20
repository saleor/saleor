from django.conf import settings
from django.contrib import messages, auth
from django.contrib.auth import views as django_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse

from saleor.cart.utils import find_and_assign_anonymous_cart
from .forms import LoginForm, SignupForm, SetPasswordForm


@find_and_assign_anonymous_cart()
def login(request):
    kwargs = {
        'template_name': 'account/login.html', 'authentication_form': LoginForm}
    return django_views.login(request, **kwargs)


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
        user = auth.authenticate(email=email, password=password)
        if user:
            auth.login(request, user)
        messages.success(request, _('User has been created'))
        return redirect(settings.LOGIN_REDIRECT_URL)
    ctx = {'form': form}
    return TemplateResponse(request, 'account/signup.html', ctx)


def password_reset(request):
    template_name = 'account/password_reset.html'
    post_reset_redirect = 'account_reset_password_done'
    email_template_name = 'account/email/password_reset_message.txt'
    subject_template_name = 'account/email/password_reset_subject.txt'
    return django_views.password_reset(
        request, template_name=template_name,
        post_reset_redirect=post_reset_redirect,
        email_template_name=email_template_name,
        subject_template_name=subject_template_name)


def password_reset_confirm(request, uidb64=None, token=None):
    template_name = 'account/password_reset_from_key.html'
    post_reset_redirect = 'account_reset_password_complete'
    set_password_form = SetPasswordForm
    return django_views.password_reset_confirm(
        request, uidb64=uidb64, token=token, template_name=template_name,
        post_reset_redirect=post_reset_redirect,
        set_password_form=set_password_form)
