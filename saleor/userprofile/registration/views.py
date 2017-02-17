from django.conf import settings
from django.contrib import messages, auth
from django.contrib.auth import views as django_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from ...cart.utils import find_and_assign_anonymous_cart
from .forms import LoginForm


@find_and_assign_anonymous_cart()
def login(request):
    next_url = request.GET.get('next')
    kwargs = {
        'template_name': 'account/login.html', 'authentication_form': LoginForm}
    if next_url:
        kwargs['redirect_authenticated_user'] = next_url
    return django_views.login(request, **kwargs)


@login_required
def logout(request):
    auth.logout(request)
    messages.success(request, _('You have been successfully logged out.'))
    return redirect(settings.LOGIN_REDIRECT_URL)
