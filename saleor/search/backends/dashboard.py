from collections import defaultdict

from . import get_search_backend
from .base import BaseSearchQuery
from ..index import get_indexed_models

CONTENT_TYPES_MAP = {
    model.indexed_get_content_type(): model
    for model in get_indexed_models()}

DEFAULT_BACKEND = get_search_backend('default')
DEFAULT_BACKEND_CLASS = DEFAULT_BACKEND.__class__
DEFAULT_BACKEND_RESULTS_CLASS = DEFAULT_BACKEND.results_class


class DashboardSearchQuery(BaseSearchQuery):

    def __init__(self, query_string,
                 fields=None, operator=None, order_by_relevance=True,
                 queryset_map=None):
        if queryset_map:
            queryset_map = {model.indexed_get_content_type(): queryset
                            for model, queryset in queryset_map.items()}
        else:
            queryset_map = {content_type: model.objects.all()
                            for content_type, model in CONTENT_TYPES_MAP.items()}
        self.queryset_map = queryset_map
        super(DashboardSearchQuery, self).__init__(
            query_string=query_string, queryset=None, fields=fields,
            operator=operator, order_by_relevance=order_by_relevance)

    def get_inner_query(self):
        if self.query_string is not None:
            fields = self.fields or ['_all', '_partials']

            if len(fields) == 1:
                if self.operator == 'or':
                    query = {
                        'match': {
                            fields[0]: self.query_string,
                        }
                    }
                else:
                    query = {
                        'match': {
                            fields[0]: {
                                'query': self.query_string,
                                'operator': self.operator,
                            }
                        }
                    }
            else:
                query = {
                    'multi_match': {
                        'query': self.query_string,
                        'fields': fields,
                    }
                }

                if self.operator != 'or':
                    query['multi_match']['operator'] = self.operator
        else:
            query = {
                'match_all': {}
            }

        return query

    def get_query(self):
        return self.get_inner_query()


class DashboardSearchResults(DEFAULT_BACKEND_RESULTS_CLASS):

    def _do_search(self):
        # Params for elasticsearch query
        params = dict(
            body=self._get_es_body(),
            _source=False,
            from_=self.start,
            index='{}*'.format(self.backend.get_index().name)
        )
        params[self.fields_param_name] = 'pk'

        # Add size if set
        if self.stop is not None:
            params['size'] = self.stop - self.start
        # Send to Elasticsearch
        hits = self.backend.es.search(**params)
        search_hits = defaultdict(list)
        scores = {}
        for hit in hits['hits']['hits']:
            hit_type = hit['_type']
            hit_pk = hit['fields']['pk'][0]
            search_hits[hit_type].append(hit_pk)
            scores[hit['_id']] = hit['_score']

        results_by_model = {}
        for content_type, hit_pks in search_hits.items():
            queryset = self.query.queryset_map[content_type]
            results_by_model[content_type] = queryset.filter(pk__in=hit_pks)

        all_results = []
        for content_type, hits in results_by_model.items():
            for hit in hits:
                score_key = '%s:%d' % (content_type, hit.pk)
                setattr(hit, 'search_score', scores[score_key])
                setattr(hit, 'content_type', content_type)
                all_results.append(hit)
        sorted_results = sorted(
            all_results, key=lambda h: h.search_score, reverse=True)
        return list(sorted_results)

    def _get_es_body(self, for_count=False):
        body = {
            'query': self.query.get_query()
        }

        if not for_count:
            sort = None

            if sort is not None:
                body['sort'] = sort

        return body

    def _do_count(self):
        # Get count
        hit_count = self.backend.es.count(
            body=self._get_es_body(for_count=True),
            index='{}*'.format(self.backend.get_index().name)
        )['count']
        # Add limits
        hit_count -= self.start
        if self.stop is not None:
            hit_count = min(hit_count, self.stop - self.start)

        return max(hit_count, 0)


class DashboardMultiTypeSearchBackend(DEFAULT_BACKEND_CLASS):
    results_class = DashboardSearchResults
    query_class = DashboardSearchQuery

    def search(self, query_string,
               model_or_queryset=None, fields=None, filters=None,
               prefetch_related=None, operator=None, order_by_relevance=True,
               queryset_map=None):
        search_query = self.query_class(
            query_string=query_string, fields=fields, operator=operator,
            order_by_relevance=order_by_relevance, queryset_map=queryset_map)
        return self.results_class(self, search_query)

SearchBackend = DashboardMultiTypeSearchBackend
