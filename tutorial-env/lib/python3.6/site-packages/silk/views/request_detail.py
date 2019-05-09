import json

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from silk.auth import login_possibly_required, permissions_possibly_required

from silk.code_generation.curl import curl_cmd
from silk.models import Request
from silk.code_generation.django_test_client import gen


class RequestView(View):

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def get(self, request, request_id):
        silk_request = Request.objects.get(pk=request_id)
        query_params = None
        if silk_request.query_params:
            query_params = json.loads(silk_request.query_params)
        body = silk_request.raw_body
        try:
            body = json.loads(body)  # Incase encoded as JSON
        except (ValueError, TypeError):
            pass
        context = {
            'silk_request': silk_request,
            'curl': curl_cmd(url=request.build_absolute_uri(silk_request.path),
                             method=silk_request.method,
                             query_params=query_params,
                             body=body,
                             content_type=silk_request.content_type),
            'query_params': json.dumps(query_params, sort_keys=True, indent=4) if query_params else None,
            'client': gen(path=silk_request.path,
                          method=silk_request.method,
                          query_params=query_params,
                          data=body,
                          content_type=silk_request.content_type),
            'request': request
        }
        return render(request, 'silk/request.html', context)
