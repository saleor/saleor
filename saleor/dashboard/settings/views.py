from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...core.models import Setting


def index(request):
    settings = Setting.objects.all()
    ctx = {'settings': settings}
    return TemplateResponse(request, 'dashboard/settings/index.html', ctx)
