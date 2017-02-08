from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from .forms import SiteSettingForm
from ..views import staff_member_required
from ...site.models import SiteSettings
from ...site.utils import get_site_settings_from_request


@staff_member_required
def index(request):
    settings = get_site_settings_from_request(request)
    return redirect('dashboard:site-update', site_id=settings.pk)


@staff_member_required
def update(request, site_id=None):
    site = get_object_or_404(SiteSettings, pk=site_id)
    form = SiteSettingForm(request.POST or None, instance=site)
    if form.is_valid():
        site = form.save()
        messages.success(request, _('Updated site %s') % site)
    ctx = {'site': site, 'form': form}
    return TemplateResponse(request, 'dashboard/sites/detail.html', ctx)
