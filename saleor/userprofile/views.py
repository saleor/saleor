from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _

from .forms import get_address_form


@login_required
def details(request):
    ctx = {'addresses': request.user.addresses.all(),
           'orders': request.user.orders.prefetch_related('groups__items')}
    return TemplateResponse(request, 'userprofile/details.html', ctx)

@login_required
def address_delete(request, pk):
    address = get_object_or_404(request.user.addresses, pk=pk)
    if request.method == 'POST':
        address.delete()
        messages.success(request, _('Address successfully deleted.'))
        return HttpResponseRedirect(reverse('profile:details'))
    return TemplateResponse(
        request, 'userprofile/address-delete.html', {'address': address})
