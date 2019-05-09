from django.db.models import Sum
from django.shortcuts import render
from django.template.context_processors import csrf
from django.utils.decorators import method_decorator
from django.views.generic import View

from silk.auth import login_possibly_required, permissions_possibly_required
from silk.models import Request, Response
from silk.request_filters import BaseFilter, filters_from_request

__author__ = 'mtford'


class RequestsView(View):
    show = [5, 10, 25, 100, 250]
    default_show = 25

    order_by = {
        'start_time': {
            'label': 'Recent',
            'additional_query_filter': None
        },
        'path': {
            'label': 'Path',
            'additional_query_filter': None
        },
        'num_sql_queries': {
            'label': 'Num. Queries',
            'additional_query_filter': None
        },
        'time_taken': {
            'label': 'Time',
            'additional_query_filter': lambda x: x.filter(time_taken__gte=0)
        },
        'db_time': {
            'label': 'Time on queries',
            'additional_query_filter': lambda x: x.annotate(db_time=Sum('queries__time_taken'))
            .filter(db_time__gte=0)
        },
    }
    order_dir = {
        'ASC': {
            'label': 'Ascending'
        },
        'DESC': {
            'label': 'Descending'
        }
    }
    default_order_by = 'start_time'
    default_order_dir = 'DESC'

    session_key_request_filters = 'request_filters'

    @property
    def options_order_by(self):
        return [{'value': x, 'label': self.order_by[x]['label']} for x in self.order_by.keys()]

    @property
    def options_order_dir(self):
        return [{'value': x, 'label': self.order_dir[x]['label']} for x in self.order_dir.keys()]

    def _get_paths(self):
        return [''] + [x['path'] for x in Request.objects.values('path').distinct()]

    def _get_status_codes(self):
        return [x['status_code'] for x in Response.objects.values('status_code').distinct()]

    def _get_methods(self):
        return [x['method'] for x in Request.objects.values('method').distinct()]

    def _get_objects(self, show=None, order_by=None, order_dir=None, path=None, filters=None):
        if not filters:
            filters = []
        if not show:
            show = self.default_show
        query_set = Request.objects.all()
        if not order_by:
            order_by = self.default_order_by
        if not order_dir:
            order_dir = self.default_order_dir
        if order_by not in self.order_by.keys():
            raise RuntimeError('Unknown order_by: "%s"' % order_by)
        ob = self.order_by[order_by]
        if ob['additional_query_filter'] is not None:
            query_set = ob['additional_query_filter'](query_set)
        query_set = query_set.order_by('%s%s' % ('-' if order_dir == 'DESC' else '', order_by))
        if path:
            query_set = query_set.filter(path=path)
        for f in filters:
            query_set = f.contribute_to_query_set(query_set)
            query_set = query_set.filter(f)
        return query_set[:show]

    def _create_context(self, request):
        show = request.GET.get('show', self.default_show)
        order_by = request.GET.get('order_by', self.default_order_by)
        order_dir = request.GET.get('order_dir', self.default_order_dir)
        if show:
            show = int(show)
        path = request.GET.get('path', None)
        raw_filters = request.session.get(self.session_key_request_filters, {})
        context = {
            'show': show,
            'order_by': order_by,
            'order_dir': order_dir,
            'request': request,
            'options_show': self.show,
            'options_order_by': self.options_order_by,
            'options_order_dir': self.options_order_dir,
            'options_paths': self._get_paths(),
            'options_status_codes': self._get_status_codes(),
            'options_methods': self._get_methods(),
            'view_names': [x[0] for x in Request.objects.values_list('view_name').distinct() if x[0]],
            'filters': raw_filters
        }
        context.update(csrf(request))
        if path:
            context['path'] = path
        context['results'] = self._get_objects(show, order_by, order_dir, path,
                                               filters=[BaseFilter.from_dict(x) for _, x in raw_filters.items()])
        return context

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def get(self, request):
        return render(request, 'silk/requests.html', self._create_context(request))

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def post(self, request):
        filters = filters_from_request(request)
        request.session[self.session_key_request_filters] = {ident: f.as_dict() for ident, f in filters.items()}
        return render(request, 'silk/requests.html', self._create_context(request))
