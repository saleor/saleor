from threading import local

import cProfile
import pstats
import logging

from django.utils.six import StringIO, with_metaclass

from silk import models
from silk.config import SilkyConfig
from silk.errors import SilkNotConfigured, SilkInternalInconsistency
from silk.models import _time_taken
from silk.singleton import Singleton

TYP_SILK_QUERIES = 'silk_queries'
TYP_PROFILES = 'profiles'
TYP_QUERIES = 'queries'

Logger = logging.getLogger('silk.collector')


def raise_middleware_error():
    raise RuntimeError(
        'Silk middleware has not been installed correctly. Ordering must ensure that Silk middleware can '
        'execute process_request and process_response. If an earlier middleware returns from either of '
        'these methods, Silk will not have the chance to inspect the request/response objects.')


class DataCollector(with_metaclass(Singleton, object)):
    """
    Provides the ability to save all models at the end of the request. We
    cannot save during the request due to the possibility of atomic blocks
    and hence must collect data and perform the save at the end.
    """

    def __init__(self):
        super(DataCollector, self).__init__()
        self.local = local()
        self._configure()

    def ensure_middleware_installed(self):
        if not hasattr(self.local, 'temp_identifier'):
            raise_middleware_error()

    @property
    def request(self):
        return getattr(self.local, 'request', None)

    def get_identifier(self):
        self.ensure_middleware_installed()
        self.local.temp_identifier += 1
        return self.local.temp_identifier

    @request.setter
    def request(self, value):
        self.local.request = value

    def _configure(self):
        self.local.objects = {}
        self.local.temp_identifier = 0
        self.local.pythonprofiler = None

    @property
    def objects(self):
        return getattr(self.local, 'objects', None)

    @property
    def queries(self):
        return self._get_objects(TYP_QUERIES)

    @property
    def silk_queries(self):
        return self._get_objects(TYP_SILK_QUERIES)

    def _get_objects(self, typ):
        objects = self.objects
        if objects is None:
            self._raise_not_configured(
                'Attempt to access %s without initialisation.' % typ
            )
        if typ not in objects:
            objects[typ] = {}
        return objects[typ]

    @property
    def profiles(self):
        return self._get_objects(TYP_PROFILES)

    def configure(self, request=None):
        silky_config = SilkyConfig()

        self.request = request
        self._configure()

        if silky_config.SILKY_PYTHON_PROFILER:
            self.local.pythonprofiler = cProfile.Profile()
            self.local.pythonprofiler.enable()

    def clear(self):
        self.request = None
        self._configure()

    def _raise_not_configured(self, err):
        raise SilkNotConfigured(err + ' Is the middleware installed correctly?')

    def register_objects(self, typ, *args):
        self.ensure_middleware_installed()
        for arg in args:
            ident = self.get_identifier()
            objects = self.objects
            if objects is None:
                # This can happen if the SilkyMiddleware.process_request is not
                # called for whatever reason. Perhaps if another piece of
                # middleware is not playing ball.
                self._raise_not_configured(
                    'Attempt to register object of type %s without initialisation. '
                )
            if typ not in objects:
                self.objects[typ] = {}
            self.objects[typ][ident] = arg

    def register_query(self, *args):
        self.register_objects(TYP_QUERIES, *args)

    def register_profile(self, *args):
        self.register_objects(TYP_PROFILES, *args)

    def _record_meta_profiling(self):
        if SilkyConfig().SILKY_META:
            num_queries = len(self.silk_queries)
            query_time = sum(_time_taken(x['start_time'], x['end_time']) for _, x in self.silk_queries.items())
            self.request.meta_num_queries = num_queries
            self.request.meta_time_spent_queries = query_time
            self.request.save()

    def stop_python_profiler(self):
        if getattr(self.local, 'pythonprofiler', None):
            self.local.pythonprofiler.disable()

    def finalise(self):
        if getattr(self.local, 'pythonprofiler', None):
            s = StringIO()
            ps = pstats.Stats(self.local.pythonprofiler, stream=s).sort_stats('cumulative')
            ps.print_stats()
            profile_text = s.getvalue()
            profile_text = "\n".join(
                profile_text.split("\n")[0:256])  # don't record too much because it can overflow the field storage size
            self.request.pyprofile = profile_text

            if SilkyConfig().SILKY_PYTHON_PROFILER_BINARY:
                file_name = self.request.prof_file.storage.get_available_name("{}.prof".format(str(self.request.id)))
                with open(self.request.prof_file.storage.path(file_name), 'w+b') as f:
                    ps.dump_stats(f.name)
                self.request.prof_file = f.name
                self.request.save()

        for _, query in self.queries.items():
            query_model = models.SQLQuery.objects.create(**query)
            query['model'] = query_model
        for _, profile in self.profiles.items():
            profile_query_models = []
            if TYP_QUERIES in profile:
                profile_queries = profile[TYP_QUERIES]
                del profile[TYP_QUERIES]
                for query_temp_id in profile_queries:
                    try:
                        query = self.queries[query_temp_id]
                        try:
                            profile_query_models.append(query['model'])
                        except KeyError:
                            raise SilkInternalInconsistency(
                                'Profile references a query dictionary that has not '
                                'been converted into a Django model. This should '
                                'never happen, please file a bug report'
                            )
                    except KeyError:
                        raise SilkInternalInconsistency(
                            'Profile references a query temp_id that does not exist. '
                            'This should never happen, please file a bug report'
                        )
            profile = models.Profile.objects.create(**profile)
            if profile_query_models:
                profile.queries = profile_query_models
                profile.save()
        self._record_meta_profiling()

    def register_silk_query(self, *args):
        self.register_objects(TYP_SILK_QUERIES, *args)
