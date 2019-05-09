import logging
import random

from django.db import transaction, DatabaseError
try:
    # Django >= 1.10
    from django.urls import reverse, NoReverseMatch
except ImportError:
    # Django < 2.0
    from django.core.urlresolvers import reverse, NoReverseMatch

from django.db.models.sql.compiler import SQLCompiler
from django.utils import timezone

from silk.collector import DataCollector

from silk.config import SilkyConfig
from silk.model_factory import RequestModelFactory, ResponseModelFactory
from silk.profiling import dynamic
from silk.profiling.profiler import silk_meta_profiler
from silk.sql import execute_sql

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django < 1.10
    # Works perfectly for everyone using MIDDLEWARE_CLASSES
    MiddlewareMixin = object


Logger = logging.getLogger('silk.middleware')


def silky_reverse(name, *args, **kwargs):
    try:
        r = reverse('silk:%s' % name, *args, **kwargs)
    except NoReverseMatch:
        # In case user forgets to set namespace, but also fixes Django 1.5 tests on Travis
        # Hopefully if user has forgotten to add namespace there are no clashes with their own
        # view names but I don't think there is really anything can do about this.
        r = reverse(name, *args, **kwargs)
    return r


fpath = silky_reverse('summary')
config = SilkyConfig()


def _should_intercept(request):
    """we want to avoid recording any requests/sql queries etc that belong to Silky"""
    # Check custom intercept logic.
    if config.SILKY_INTERCEPT_FUNC:
        if not config.SILKY_INTERCEPT_FUNC(request):
            return False
    # don't trap every request
    elif config.SILKY_INTERCEPT_PERCENT < 100:
        if random.random() > config.SILKY_INTERCEPT_PERCENT / 100.0:
            return False

    silky = request.path.startswith(fpath)
    ignored = request.path in config.SILKY_IGNORE_PATHS
    return not (silky or ignored)


class TestMiddleware(object):
    def process_response(self, request, response):
        return response

    def process_request(self, request):
        return


class SilkyMiddleware(MiddlewareMixin):
    def _apply_dynamic_mappings(self):
        dynamic_profile_configs = config.SILKY_DYNAMIC_PROFILING
        for conf in dynamic_profile_configs:
            module = conf.get('module')
            function = conf.get('function')
            start_line = conf.get('start_line')
            end_line = conf.get('end_line')
            name = conf.get('name')
            if module and function:
                if start_line and end_line:  # Dynamic context manager
                    dynamic.inject_context_manager_func(module=module,
                                                        func=function,
                                                        start_line=start_line,
                                                        end_line=end_line,
                                                        name=name)
                else:  # Dynamic decorator
                    dynamic.profile_function_or_method(module=module,
                                                       func=function,
                                                       name=name)
            else:
                raise KeyError('Invalid dynamic mapping %s' % conf)

    @silk_meta_profiler()
    def process_request(self, request):
        DataCollector().clear()

        if not _should_intercept(request):
            return

        Logger.debug('process_request')
        request.silk_is_intercepted = True
        self._apply_dynamic_mappings()
        if not hasattr(SQLCompiler, '_execute_sql'):
            SQLCompiler._execute_sql = SQLCompiler.execute_sql
            SQLCompiler.execute_sql = execute_sql
        request_model = RequestModelFactory(request).construct_request_model()
        DataCollector().configure(request_model)

    @transaction.atomic()
    def _process_response(self, request, response):
        Logger.debug('Process response')
        with silk_meta_profiler():
            collector = DataCollector()
            collector.stop_python_profiler()
            silk_request = collector.request
            if silk_request:
                silk_response = ResponseModelFactory(response).construct_response_model()
                silk_response.save()
                silk_request.end_time = timezone.now()
                collector.finalise()
            else:
                Logger.error(
                    'No request model was available when processing response. '
                    'Did something go wrong in process_request/process_view?'
                    '\n' + str(request) + '\n\n' + str(response)
                )
        # Need to save the data outside the silk_meta_profiler
        # Otherwise the  meta time collected in the context manager
        # is not taken in account
        if silk_request:
            silk_request.save()
        Logger.debug('Process response done.')

    def process_response(self, request, response):
        if getattr(request, 'silk_is_intercepted', False):
            while True:
                try:
                    self._process_response(request, response)
                except (AttributeError, DatabaseError):
                    Logger.debug('Retrying _process_response')
                    self._process_response(request, response)
                finally:
                    break
        return response
