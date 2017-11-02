from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from .forms import AuthorizationKeyFormSet, SiteForm, SiteSettingForm
from ..views import superuser_required
from ...site.models import AuthorizationKey, SiteSettings


@superuser_required
def index(request):
    settings = get_current_site(request).settings
    return redirect('dashboard:site-update', site_id=settings.pk)


@superuser_required
def update(request, site_id=None):
    site_settings = get_object_or_404(SiteSettings, pk=site_id)
    site = site_settings.site
    site_settings_form = SiteSettingForm(
        request.POST or None, instance=site_settings)
    site_form = SiteForm(request.POST or None, instance=site)
    authorization_qs = AuthorizationKey.objects.filter(
        site_settings=site_settings)
    formset = AuthorizationKeyFormSet(
        request.POST or None, queryset=authorization_qs,
        initial=[{'site_settings': site_settings}])
    if all([site_settings_form.is_valid(), site_form.is_valid(),
            formset.is_valid()]):
        site = site_form.save()
        site_settings_form.instance.site = site
        site_settings = site_settings_form.save()
        formset.save()
        messages.success(request, _('Updated site %s') % site_settings)
        return redirect('dashboard:site-update', site_id=site_settings.id)
    ctx = {'site': site_settings, 'site_settings_form': site_settings_form,
           'site_form': site_form, 'formset': formset}
    return TemplateResponse(request, 'dashboard/sites/detail.html', ctx)
