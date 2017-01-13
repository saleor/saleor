from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...site.models import Setting
from .forms import SettingForm


def index(request):
    settings = Setting.objects.all()
    ctx = {'settings': settings}
    return TemplateResponse(request, 'dashboard/settings/index.html', ctx)


def create(request):
    form = SettingForm(request.POST or None)
    if form.is_valid():
        setting = form.save()
        messages.success(request, _('Added site %s') % setting)
        return redirect('dashboard:site-index')
    ctx = {'form': form}
    return TemplateResponse(request, 'dashboard/settings/detail.html', ctx)
