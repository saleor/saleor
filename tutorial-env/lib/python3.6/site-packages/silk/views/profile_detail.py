from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from silk.auth import login_possibly_required, permissions_possibly_required
from silk.models import Profile
from silk.views.code import _code_context, _code_context_from_request


class ProfilingDetailView(View):

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def get(self, request, *_, **kwargs):
        profile_id = kwargs['profile_id']
        context = {
            'request': request
        }
        profile = Profile.objects.get(pk=profile_id)
        file_path = profile.file_path
        line_num = profile.line_num

        context['pos'] = pos = int(request.GET.get('pos', 0))
        if pos:
            context.update(_code_context_from_request(request, prefix='pyprofile_'))

        context['profile'] = profile
        context['line_num'] = file_path
        context['file_path'] = line_num
        context['file_column'] = 5

        if profile.request:
            context['silk_request'] = profile.request
        if file_path and line_num:
            try:
                context.update(_code_context(file_path, line_num, profile.end_line_num))
            except IOError as e:
                if e.errno == 2:
                    context['code_error'] = e.filename + ' does not exist.'
                else:
                    raise e

        return render(request, 'silk/profile_detail.html', context)
