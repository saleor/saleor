from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...site.models import SiteSetting
from ..views import staff_member_required
from .forms import SiteSettingForm


@staff_member_required
def index(request):
    sites = SiteSetting.objects.all()
    ctx = {'sites': sites}
    return TemplateResponse(request, 'dashboard/sites/index.html', ctx)


@staff_member_required
def create(request):
    form = SiteSettingForm(request.POST or None)
    if form.is_valid():
        site = form.save()
        messages.success(request, _('Added site %s') % site)
        return redirect('dashboard:site-index')
    ctx = {'form': form}
    return TemplateResponse(request, 'dashboard/sites/detail.html', ctx)


@staff_member_required
def update(request, site_id=None):
    site = get_object_or_404(SiteSetting, pk=site_id)
    form = SiteSettingForm(request.POST or None, instance=site)
    if form.is_valid():
        site = form.save()
        messages.success(request, _('Updated site %s') % site)
    ctx = {'site': site, 'form': form}
    return TemplateResponse(request, 'dashboard/sites/detail.html', ctx)


@staff_member_required
def delete(request, site_id=None):
    site = get_object_or_404(SiteSetting, pk=site_id)
    if request.method == 'POST':
        site.delete()
        messages.success(request, _('Delete site %s') % site)
        if request.is_ajax():
            response = {'redirectUrl': reverse(
                'dashboard:site-index')}
            return JsonResponse(response)
        return redirect('dashboard:site-index')
    ctx = {'site': site}
    return TemplateResponse(request, 'dashboard/sites/delete_modal.html', ctx)
