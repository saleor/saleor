from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .models import Address
from .forms import AddressFormWithAlias


@login_required
def details(request):

    ctx = {'addresses': request.user.addressbook.all()}
    return TemplateResponse(request, "userprofile/details.html", ctx)


def validate_address_and_render(request, form, success_message):
    if form.is_valid():
        address = form.save()
        messages.success(request, success_message % address)
        return HttpResponseRedirect(reverse("profile:details"))

    return TemplateResponse(
        request,
        "userprofile/address-edit.html",
        {'form': form, })


@login_required
def address_edit(request, slug, pk):

    address = get_object_or_404(Address, pk=pk, user=request.user)

    if not address.get_slug() == slug and request.method == "GET":
        return HttpResponseRedirect(address.get_absolute_url())

    if request.POST:
        form = AddressFormWithAlias(request.POST, instance=address)
    else:
        form = AddressFormWithAlias(instance=address)

    message = "Successfully updated address '%s'."

    return validate_address_and_render(request, form, success_message=message)


@login_required
def address_create(request):

    if request.POST:
        form = AddressFormWithAlias(request.POST,
                                    instance=Address(user=request.user))
    else:
        form = AddressFormWithAlias()

    message = "Successfully created address '%s'."

    return validate_address_and_render(request, form, success_message=message)


@login_required
def address_delete(request, slug, pk):

    address = get_object_or_404(Address, pk=pk, user=request.user)

    if not address.get_slug() == slug and request.method == "GET":
        return HttpResponseRedirect(address.get_absolute_url())

    if request.POST:
        address.delete()
        message = "Successfully deleted address '%s'."
        messages.success(request, message % address)
        return HttpResponseRedirect(reverse("profile:details"))

    return TemplateResponse(request, "userprofile/address-delete.html")
