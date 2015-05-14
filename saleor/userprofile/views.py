from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _

from .forms import AddressForm


@login_required
def details(request):

    ctx = {'address_book': request.user.address_book.all()}
    return TemplateResponse(request, 'userprofile/details.html', ctx)


@login_required
def orders(request):

    ctx = {'orders': request.user.orders.prefetch_related('groups')}
    return TemplateResponse(request, 'userprofile/orders.html', ctx)


@login_required
def address_edit(request, slug, pk):
    address = get_object_or_404(request.user.addresses, pk=pk)
    address_form = AddressForm(request.POST or None, instance=address)
    if address_form.is_valid():
        address_form.save()
        message = _('Address successfully updated.')
        messages.success(request, message)
        return HttpResponseRedirect(reverse('profile:details'))
    return TemplateResponse(
        request, 'userprofile/address-edit.html',
        {'address_form': address_form})

@login_required
def address_create(request):
    user = request.user
    is_first_address = not user.addresses.exists()
    address_form = AddressForm(request.POST or None)
    if address_form.is_valid():
        address = address_form.save()
        user.addresses.add(address)
        user.default_shipping_address = address
        user.default_billing_address = address
        user.save(update_fields=[
            'default_shipping_address', 'default_billing_address'])
        message = _('Address successfully created.')
        messages.success(request, message)
        return HttpResponseRedirect(reverse('profile:details'))
    return TemplateResponse(
        request, 'userprofile/address-edit.html',
        {'address_form': address_form})


@login_required
def address_delete(request, slug, pk):
    address = get_object_or_404(request.user.addresses, pk=pk)
    if request.method == 'POST':
        address.delete()
        messages.success(request, _('Address successfully deleted.'))
        return HttpResponseRedirect(reverse('profile:details'))
    return TemplateResponse(
        request, 'userprofile/address-delete.html', {'object': address})


@login_required
@require_POST
def address_make_default(request, pk, purpose):
    user = request.user
    address = get_object_or_404(user.addresses, pk=pk)
    if purpose == 'shipping':
        user.default_shipping_address = address
        user.save(update_fields=['default_shipping_address'])
    elif purpose == 'billing':
        user.default_billing_address = address
        user.save(update_fields=['default_billing_address'])
    else:
        raise Http404('Unknown purpose')
    return redirect('profile:details')
