from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST

from .models import AddressBook
from .forms import AddressBookForm, AddressForm


@login_required
def details(request):

    ctx = {'address_book': request.user.address_book.all()}
    return TemplateResponse(request, "userprofile/details.html", ctx)


def validate_address_and_render(request, address_form, address_book_form,
                                success_message):
    if address_form.is_valid() and address_book_form.is_valid():
        address = address_form.save()
        address_book_form.instance.address = address
        address_book = address_book_form.save()
        messages.success(request, success_message % address_book)
        return HttpResponseRedirect(reverse("profile:details"))

    return TemplateResponse(
        request,
        "userprofile/address-edit.html",
        {'address_form': address_form, 'address_book_form': address_book_form})


@login_required
def address_edit(request, slug, pk):

    address_book = get_object_or_404(AddressBook, pk=pk, user=request.user)
    address = address_book.address

    if not address_book.get_slug() == slug and request.method == "GET":
        return HttpResponseRedirect(address_book.get_absolute_url())

    if request.POST:
        address_form = AddressForm(request.POST, instance=address)
        address_book_form = AddressBookForm(
            request.POST, instance=address_book)
    else:
        address_form = AddressForm(instance=address)
        address_book_form = AddressBookForm(instance=address_book)

    message = "Successfully updated address '%s'."

    return validate_address_and_render(
        request, address_form, address_book_form, success_message=message)


@login_required
def address_create(request):

    if request.POST:
        address_form = AddressForm(request.POST)
        address_book_form = AddressBookForm(
            request.POST, instance=AddressBook(user=request.user))
    else:
        address_form = AddressForm()
        address_book_form = AddressBookForm()

    message = "Successfully created address '%s'."

    return validate_address_and_render(
        request, address_form, address_book_form, success_message=message)


@login_required
def address_delete(request, slug, pk):

    address_book = get_object_or_404(AddressBook, pk=pk, user=request.user)

    if not address_book.get_slug() == slug:
        raise Http404

    if request.POST:
        address_book.address.delete()
        message = "Successfully deleted address '%s'."
        messages.success(request, message % address_book)
        return HttpResponseRedirect(reverse("profile:details"))

    return TemplateResponse(request, "userprofile/address-delete.html")


@login_required
@require_POST
def address_make_default(request, pk, purpose):
    user = request.user

    address_book = get_object_or_404(AddressBook, pk=pk, user=user)

    if purpose == 'shipping':
        user.default_shipping_address = address_book
    elif purpose == 'billing':
        user.default_billing_address = address_book
    else:
        raise AssertionError(
            "``purpose`` should be ``billing`` or ``shipping``")

    user.save()

    return redirect('profile:details')
