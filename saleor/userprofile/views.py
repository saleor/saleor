from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import pgettext
from .forms import (ChangePasswordForm, get_address_form,
                    logout_on_password_change)
from django.utils.translation import ugettext_lazy as _

from ..wishlist.forms import WishlistSettingsForm
from ..wishlist.models import Wishlist


@login_required
def details(request):
    password_form = get_or_process_password_form(request)
    wishlist_form = get_or_process_wishlist_form(request)
    ctx = {'addresses': request.user.addresses.all(),
           'orders': request.user.orders.prefetch_related('groups__items'),
           'change_password_form': password_form,
           'wishlist_form': wishlist_form
           }

    return TemplateResponse(request, 'userprofile/details.html', ctx)


def get_or_process_password_form(request):
    form = ChangePasswordForm(data=request.POST or None, user=request.user)
    if form.is_valid():
        form.save()
        logout_on_password_change(request, form.user)
        messages.success(request, pgettext(
            'Storefront message', 'Password successfully changed.'))
    return form


def get_or_process_wishlist_form(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    if 'wishlist_form' in request.POST:
        data = request.POST
    else:
        data = None
    form = WishlistSettingsForm(instance=wishlist, data=data,
                                prefix='wishlist')
    if form.is_valid():
        form.save()
        messages.success(request, _('Wishlist settings saved.'))
    return form


@login_required
def address_edit(request, pk):
    address = get_object_or_404(request.user.addresses, pk=pk)
    address_form, preview = get_address_form(
        request.POST or None, instance=address,
        country_code=address.country.code)
    if address_form.is_valid() and not preview:
        address_form.save()
        message = pgettext('Storefront message', 'Address successfully updated.')
        messages.success(request, message)
        return HttpResponseRedirect(reverse('profile:details') + '#addresses')
    return TemplateResponse(
        request, 'userprofile/address-edit.html',
        {'address_form': address_form})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(request.user.addresses, pk=pk)
    if request.method == 'POST':
        address.delete()
        messages.success(
            request,
            pgettext('Storefront message', 'Address successfully deleted.'))
        return HttpResponseRedirect(reverse('profile:details') + '#addresses')
    return TemplateResponse(
        request, 'userprofile/address-delete.html', {'address': address})
