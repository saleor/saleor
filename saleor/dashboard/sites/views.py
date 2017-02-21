from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from .forms import AuthorizationKeyFormSet, SiteSettingForm
from ..views import staff_member_required
from ...site.models import AuthorizationKey, SiteSettings
from ...site.utils import get_site_settings_from_request


@staff_member_required
def index(request):
    settings = get_site_settings_from_request(request)
    return redirect('dashboard:site-update', site_id=settings.pk)


@staff_member_required
def update(request, site_id=None):
    site = get_object_or_404(SiteSettings, pk=site_id)
    form = SiteSettingForm(request.POST or None, instance=site)
    authorization_qs = AuthorizationKey.objects.filter(site_settings=site)
    formset = AuthorizationKeyFormSet(
        request.POST or None, queryset=authorization_qs,
        initial=[{'site_settings': site}])
    if all([form.is_valid(), formset.is_valid()]):
        site = form.save()
        formset.save()
        messages.success(request, _('Updated site %s') % site)
        return redirect('dashboard:site-update', site_id=site.id)
    ctx = {'site': site, 'form': form, 'formset': formset}
    return TemplateResponse(request, 'dashboard/sites/detail.html', ctx)
