from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from silk.auth import login_possibly_required, permissions_possibly_required
from silk.models import Request, SQLQuery, Profile
from silk.utils.pagination import _page

__author__ = 'mtford'


class SQLView(View):

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def get(self, request, *_, **kwargs):
        request_id = kwargs.get('request_id')
        profile_id = kwargs.get('profile_id')
        context = {
            'request': request,
        }
        if request_id:
            silk_request = Request.objects.get(id=request_id)
            query_set = SQLQuery.objects.filter(request=silk_request).order_by('-start_time')
            for q in query_set:
                q.start_time_relative = q.start_time - silk_request.start_time
            page = _page(request, query_set)
            context['silk_request'] = silk_request
        if profile_id:
            p = Profile.objects.get(id=profile_id)
            page = _page(request, p.queries.order_by('-start_time').all())
            context['profile'] = p
        if not (request_id or profile_id):
            raise KeyError('no profile_id or request_id')
        # noinspection PyUnboundLocalVariable
        context['items'] = page
        return render(request, 'silk/sql.html', context)
