from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import views as django_views
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import pgettext, ugettext_lazy as _
from django.views.decorators.http import require_POST

from ..account.models import User
from ..checkout.utils import find_and_assign_anonymous_cart
from ..core.utils import get_paginator_items
from .emails import send_account_delete_confirmation_email
from .forms import (
    ChangePasswordForm, LoginForm, PasswordResetForm, SignupForm,
    get_address_form, logout_on_password_change, EmailChangeForm)


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
        messages.success(request, _('User has been created'))
        redirect_url = request.POST.get('next', settings.LOGIN_REDIRECT_URL)
        return redirect(redirect_url)
    ctx = {'form': form}
    return TemplateResponse(request, 'account/signup.html', ctx)


def password_reset(request):
    kwargs = {
        'template_name': 'account/password_reset.html',
        'success_url': reverse_lazy('account:reset-password-done'),
        'form_class': PasswordResetForm}
    return django_views.PasswordResetView.as_view(**kwargs)(request, **kwargs)


class PasswordResetConfirm(django_views.PasswordResetConfirmView):
    template_name = 'account/password_reset_from_key.html'
    success_url = reverse_lazy('account:reset-password-complete')
    token = None
    uidb64 = None


def password_reset_confirm(request, uidb64=None, token=None):
    kwargs = {
        'template_name': 'account/password_reset_from_key.html',
        'success_url': reverse_lazy('account:reset-password-complete'),
        'token': token,
        'uidb64': uidb64}
    return PasswordResetConfirm.as_view(**kwargs)(request, **kwargs)


@login_required
def details(request):
    email_form, password_form = get_forms_by_method_or_button(request)
    orders = request.user.orders.confirmed().prefetch_related('lines')
    orders_paginated = get_paginator_items(
        orders, settings.PAGINATE_BY, request.GET.get('page'))
    ctx = {'addresses': request.user.addresses.all(),
           'orders': orders_paginated,
           'change_password_form': password_form,
           'change_email_form': email_form}

    return TemplateResponse(request, 'account/details.html', ctx)


def get_forms_by_method_or_button(request):
    if request.method == 'POST':
        if 'email_change' in request.POST:
            password_form = ChangePasswordForm(data=None, user=request.user)
            email_form = email_edit(request)
        elif 'password_change' in request.POST:
            password_form = get_or_process_password_form(request)
            email_form = EmailChangeForm(data=None)
        return email_form, password_form
    return email_edit(request), get_or_process_password_form(request)


def get_or_process_password_form(request):
    form = ChangePasswordForm(data=request.POST or None, user=request.user)
    if form.is_valid():
        form.save()
        logout_on_password_change(request, form.user)
        messages.success(request, pgettext(
            'Storefront message', 'Password successfully changed.'))
    return form


@login_required
def address_edit(request, pk):
    address = get_object_or_404(request.user.addresses, pk=pk)
    address_form, preview = get_address_form(
        request.POST or None, instance=address,
        country_code=address.country.code)
    if address_form.is_valid() and not preview:
        address_form.save()
        message = pgettext(
            'Storefront message', 'Address successfully updated.')
        messages.success(request, message)
        return HttpResponseRedirect(reverse('account:details') + '#addresses')
    return TemplateResponse(
        request, 'account/address_edit.html',
        {'address_form': address_form})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(request.user.addresses, pk=pk)
    if request.method == 'POST':
        address.delete()
        messages.success(
            request,
            pgettext('Storefront message', 'Address successfully removed'))
        return HttpResponseRedirect(reverse('account:details') + '#addresses')
    return TemplateResponse(
        request, 'account/address_delete.html', {'address': address})


@login_required
@require_POST
def account_delete(request):
    user = request.user
    send_account_delete_confirmation_email.delay(str(user.token), user.email)
    messages.success(
        request, pgettext(
            'Storefront message, when user requested his account removed',
            'Please check your inbox for a confirmation e-mail.'))
    return HttpResponseRedirect(reverse('account:details') + '#settings')


@login_required
def account_delete_confirm(request, token):
    user = request.user

    if str(request.user.token) != token:
        raise Http404('No such page!')

    if request.method == 'POST':
        user.delete()
        msg = pgettext(
            'Account deleted',
            'Your account was deleted successfully. '
            'In case of any trouble or questions feel free to contact us.')
        messages.success(request, msg)
        return redirect('home')

    return TemplateResponse(
        request, 'account/account_delete_prompt.html')


@login_required
def email_edit(request):
    form = EmailChangeForm(data=request.POST or None, instance=request.user)

    if request.method == 'POST' and form.is_valid():
        cache.set(
            str(request.user.pk) + '_email_field', form.data['user_email'],
            1200)
        form.send_mail()
        request.user.email_change_requested_on = timezone.now()
        request.user.save()
        messages.success(
            request,
            pgettext(
                'Storefront message',
                'Email change confirmation was sent to user.'
                'Confirmation token is active only for 20 minutes.'
            ))
    return form


@login_required
def email_change_confirm(request, token=None):
    if str(request.user.token) != token:
        raise Http404('No such page!')
    new_email = cache.get(str(request.user.pk) + '_email_field')
    if new_email:
        try:
            user_exist = User.objects.get(email=new_email)
        except User.DoesNotExist:
            user_exist = None
        if user_exist:
            msg = pgettext(
                'Email changed error', 'User with this email already exists.')
        else:
            request.user.email = new_email
            request.user.save()
            cache.delete(str(request.user.pk))
            msg = pgettext(
                'Email changed success',
                'Your email address was changed successfully.')
    else:
        msg = pgettext(
            'Email changed error', 'It looks like Your token has expired.')
    return TemplateResponse(
        request, 'account/email_change_confirm.html', {'message': msg})
