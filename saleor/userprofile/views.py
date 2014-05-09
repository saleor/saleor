from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _

from .models import AddressBook, Address
from .forms import AddressBookForm, AddressForm


@login_required
def details(request):

    ctx = {'address_book': request.user.address_book.all()}
    return TemplateResponse(request, 'userprofile/details.html', ctx)


@login_required
def orders(request):

    ctx = {'orders': request.user.orders.prefetch_related('groups')}
    return TemplateResponse(request, 'userprofile/orders.html', ctx)


def validate_address_and_render(request, address_form, address_book_form,
                                success_message):
    if address_form.is_valid() and address_book_form.is_valid():
        address = address_form.save()
        address_book_form.instance.address = address
        address_book_form.save()
        messages.success(request, success_message)
        return HttpResponseRedirect(reverse('profile:details'))

    return TemplateResponse(
        request,
        'userprofile/address-edit.html',
        {'address_form': address_form, 'address_book_form': address_book_form})


@login_required
def address_edit(request, slug, pk):

    address_book = get_object_or_404(AddressBook, pk=pk, user=request.user)
    address = address_book.address

    if not address_book.get_slug() == slug and request.method == 'GET':
        return HttpResponseRedirect(address_book.get_absolute_url())

    address_form = AddressForm(request.POST or None, instance=address)
    address_book_form = AddressBookForm(
        request.POST or None, instance=address_book)

    message = _('Address successfully updated.')

    return validate_address_and_render(
        request, address_form, address_book_form, success_message=message)


@login_required
def address_create(request):

    address_form = AddressForm(request.POST or None)
    address_book_form = AddressBookForm(
        request.POST or None, instance=AddressBook(user=request.user))

    message = _('Address successfully created.')

    is_first_address = not Address.objects.exists()
    response = validate_address_and_render(
        request, address_form, address_book_form, success_message=message)
    address_book = address_book_form.instance
    if address_book.pk and is_first_address:
        user = request.user
        user.default_shipping_address = address_book
        user.default_billing_address = address_book
        user.save(update_fields=[
            'default_shipping_address', 'default_billing_address'])
    return response


@login_required
def address_delete(request, slug, pk):

    address_book = get_object_or_404(AddressBook, pk=pk, user=request.user)

    if not address_book.get_slug() == slug:
        raise Http404

    if request.method == 'POST':
        address_book.address.delete()
        messages.success(request, _('Address successfully deleted.'))
        return HttpResponseRedirect(reverse('profile:details'))

    return TemplateResponse(request, 'userprofile/address-delete.html',
                            context={'object': address_book})


@login_required
@require_POST
def address_make_default(request, pk, purpose):
    user = request.user

    address_book = get_object_or_404(AddressBook, pk=pk, user=user)
    if purpose == 'shipping':
        user.default_shipping_address = address_book
        user.save(update_fields=['default_shipping_address'])
    elif purpose == 'billing':
        user.default_billing_address = address_book
        user.save(update_fields=['default_billing_address'])
    else:
        raise AssertionError(
            '``purpose`` should be ``billing`` or ``shipping``')

    return redirect('profile:details')
