from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...site.models import Setting
from ..views import staff_member_required
from .forms import SettingForm


@staff_member_required
def index(request):
    settings = Setting.objects.all()
    ctx = {'settings': settings}
    return TemplateResponse(request, 'dashboard/sites/index.html', ctx)


@staff_member_required
def create(request):
    form = SettingForm(request.POST or None)
    if form.is_valid():
        setting = form.save()
        messages.success(request, _('Added site %s') % setting)
        return redirect('dashboard:site-index')
    ctx = {'form': form}
    return TemplateResponse(request, 'dashboard/sites/detail.html', ctx)
