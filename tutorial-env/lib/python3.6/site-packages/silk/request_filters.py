"""
Django queryset filters used by the requests view
"""
from datetime import timedelta, datetime
import logging

from django.db.models import Q, Count, Sum
from django.utils import timezone
from silk.profiling.dynamic import _get_module

from silk.templatetags.silk_filters import _silk_date_time
logger = logging.getLogger('silk.request_filters')


class FilterValidationError(Exception):
    pass


class BaseFilter(Q):
    def __init__(self, value=None, *args, **kwargs):
        self.value = value
        super(BaseFilter, self).__init__(*args, **kwargs)

    @property
    def typ(self):
        return self.__class__.__name__

    @property
    def serialisable_value(self):
        return self.value

    def as_dict(self):
        return {'typ': self.typ, 'value': self.serialisable_value, 'str': str(self)}

    @staticmethod
    def from_dict(d):
        typ = d['typ']
        filter_class = globals()[typ]
        val = d.get('value', None)
        return filter_class(val)

    def contribute_to_query_set(self, query_set):
        """
        make any changes to the query-set before the query is applied,
        e.g. annotate with extra fields
        :param query_set: a django queryset
        :return: a new query set that this filter can then be used with
        """
        return query_set


class SecondsFilter(BaseFilter):
    def __init__(self, n):
        if n:
            try:
                value = int(n)
            except ValueError as e:
                raise FilterValidationError(e)
            now = timezone.now()
            frm_dt = now - timedelta(seconds=value)
            super(SecondsFilter, self).__init__(value, start_time__gt=frm_dt)
        else:
            # Empty query
            super(SecondsFilter, self).__init__()

    def __str__(self):
        return '>%d seconds ago' % self.value


def _parse(dt, fmt):
    """attempt to coerce dt into a datetime given fmt, otherwise raise
    a FilterValidationError"""
    try:
        dt = datetime.strptime(dt, fmt)
    except TypeError:
        if not isinstance(dt, datetime):
            raise FilterValidationError('Must be a datetime object')
    except ValueError as e:
        raise FilterValidationError(e)
    return dt


class BeforeDateFilter(BaseFilter):
    fmt = '%Y/%m/%d %H:%M'

    def __init__(self, dt):
        value = _parse(dt, self.fmt)
        super(BeforeDateFilter, self).__init__(value, start_time__lt=value)

    @property
    def serialisable_value(self):
        return self.value.strftime(self.fmt)

    def __str__(self):
        return '<%s' % _silk_date_time(self.value)


class AfterDateFilter(BaseFilter):
    fmt = '%Y/%m/%d %H:%M'

    def __init__(self, dt):
        value = _parse(dt, self.fmt)
        super(AfterDateFilter, self).__init__(value, start_time__gt=value)

    @property
    def serialisable_value(self):
        return self.value.strftime(self.fmt)

    def __str__(self):
        return '>%s' % _silk_date_time(self.value)


class ViewNameFilter(BaseFilter):
    """filter on the name of the view, e.g. the name=xyz component of include in urls.py"""

    def __init__(self, view_name):
        value = view_name
        super(ViewNameFilter, self).__init__(value, view_name=view_name)

    def __str__(self):
        return 'View == %s' % self.value


class PathFilter(BaseFilter):
    """filter on path e.g. /path/to/something"""

    def __init__(self, path):
        value = path
        super(PathFilter, self).__init__(value, path=path)

    def __str__(self):
        return 'Path == %s' % self.value


class NameFilter(BaseFilter):
    def __init__(self, name):
        value = name
        super(NameFilter, self).__init__(value, name=name)

    def __str__(self):
        return 'name == %s' % self.value


class FunctionNameFilter(BaseFilter):
    def __init__(self, func_name):
        value = func_name
        super(FunctionNameFilter, self).__init__(value, func_name=func_name)

    def __str__(self):
        return 'func_name == %s' % self.value


class NumQueriesFilter(BaseFilter):
    def __init__(self, n):
        try:
            value = int(n)
        except ValueError as e:
            raise FilterValidationError(e)
        super(NumQueriesFilter, self).__init__(value, num_queries__gte=n)

    def __str__(self):
        return '#queries >= %s' % self.value

    def contribute_to_query_set(self, query_set):
        return query_set.annotate(num_queries=Count('queries'))


class TimeSpentOnQueriesFilter(BaseFilter):
    def __init__(self, n):
        try:
            value = int(n)
        except ValueError as e:
            raise FilterValidationError(e)
        super(TimeSpentOnQueriesFilter, self).__init__(value, db_time__gte=n)

    def __str__(self):
        return 'DB Time >= %s' % self.value

    def contribute_to_query_set(self, query_set):
        return query_set.annotate(db_time=Sum('queries__time_taken'))


class OverallTimeFilter(BaseFilter):
    def __init__(self, n):
        try:
            value = int(n)
        except ValueError as e:
            raise FilterValidationError(e)
        super(OverallTimeFilter, self).__init__(value, time_taken__gte=n)

    def __str__(self):
        return 'Time >= %s' % self.value


class StatusCodeFilter(BaseFilter):
    def __init__(self, n):
        try:
            value = int(n)
        except ValueError as e:
            raise FilterValidationError(e)
        super(StatusCodeFilter, self).__init__(value, response__status_code=n)


class MethodFilter(BaseFilter):
    def __init__(self, value):
        super(MethodFilter, self).__init__(value, method=value)


def filters_from_request(request):
    raw_filters = {}
    for key in request.POST:
        splt = key.split('-')
        if splt[0].startswith('filter'):
            ident = splt[1]
            typ = splt[2]
            if ident not in raw_filters:
                raw_filters[ident] = {}
            raw_filters[ident][typ] = request.POST[key]
    filters = {}
    for ident, raw_filter in raw_filters.items():
        value = raw_filter.get('value', '')
        if value.strip():
            typ = raw_filter['typ']
            module = _get_module('silk.request_filters')
            filter_class = getattr(module, typ)
            try:
                f = filter_class(value)
                filters[ident] = f
            except FilterValidationError:
                logger.warn('Validation error when processing filter %s(%s)' % (typ, value))
    return filters
