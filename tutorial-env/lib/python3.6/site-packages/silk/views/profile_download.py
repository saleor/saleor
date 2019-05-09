from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View
from silk.auth import login_possibly_required, permissions_possibly_required
from silk.models import Request


class ProfileDownloadView(View):

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def get(self, request, request_id):
        silk_request = get_object_or_404(Request, pk=request_id, prof_file__isnull=False)
        response = FileResponse(silk_request.prof_file)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(silk_request.prof_file.name)
        return response
