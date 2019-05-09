from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from silk.auth import login_possibly_required, permissions_possibly_required
from silk.models import Request
import logging
Logger = logging.getLogger('silk.views.raw')


class Raw(View):

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def get(self, request, request_id):
        typ = request.GET.get('typ', None)
        subtyp = request.GET.get('subtyp', None)
        body = None
        if typ and subtyp:
            silk_request = Request.objects.get(pk=request_id)
            if typ == 'request':
                body = silk_request.raw_body if subtyp == 'raw' else silk_request.body
            elif typ == 'response':
                Logger.debug(silk_request.response.raw_body_decoded)
                body = silk_request.response.raw_body_decoded if subtyp == 'raw' else silk_request.response.body
            return render(request, 'silk/raw.html', {
                'body': body
            })
        else:
            return HttpResponse(content='Bad Request', status=400)
