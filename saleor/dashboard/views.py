import json
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator


def index(request):
    return TemplateResponse(request, 'dashboard/index.html')


class StaffMemberOnlyMixin(object):
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(StaffMemberOnlyMixin, self).dispatch(*args, **kwargs)


class FilterByStatusMixin(object):
    def __init__(self, *args, **kwargs):
        super(FilterByStatusMixin, self).__init__(*args, **kwargs)
        status_choices = getattr(self, 'status_choices')
        self.statuses = {status[0]: status[1] for status in status_choices}

    def get_queryset(self):
        qs = super(FilterByStatusMixin, self).get_queryset()
        if self.statuses:
            active_filter = self.request.GET.get('status')
            if active_filter in self.statuses:
                qs = qs.filter(status=active_filter)
                self.active_filter = active_filter
            else:
                self.active_filter = None
        return qs

    def get_context_data(self):
        ctx = super(FilterByStatusMixin, self).get_context_data()
        ctx['active_filter'] = self.active_filter
        ctx['available_filters'] = self.statuses
        return ctx
