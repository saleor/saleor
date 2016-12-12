from . import elasticsearch2


class DashboardSearchQuery(elasticsearch2.Elasticsearch2SearchQuery):

    def __init__(self, *args, **kwargs):
        super(DashboardSearchQuery, self).__init__(*args, **kwargs)

    def get_filters(self):
        # Don't apply content type filter

        filters = []
        # Apply filters from queryset
        queryset_filters = self._get_filters_from_queryset()
        if queryset_filters:
            filters.append(queryset_filters)

        return filters


class DashboardSearchResults(elasticsearch2.Elasticsearch2SearchResults):

    def _do_search(self):
        # Params for elasticsearch query
        params = dict(
            body=self._get_es_body(),
            _source=False,
            from_=self.start,
        )
        params[self.fields_param_name] = 'pk'

        # Add size if set
        if self.stop is not None:
            params['size'] = self.stop - self.start
        # Send to Elasticsearch
        hits = self.backend.es.search(**params)
        from collections import defaultdict
        search_hits = defaultdict(list)
        scores = {}
        for hit in hits['hits']['hits']:
            hit_type = hit['_type']
            hit_pk = hit['fields']['pk'][0]
            search_hits[hit_type].append(hit_pk)
            scores[hit['_id']] = hit['_score']

        from ..index import get_indexed_models
        queryset_map = {model.indexed_get_content_type(): model.objects.all()
                        for model in get_indexed_models()}
        results_by_model = {}
        for content_type, hit_pks in search_hits.items():
            queryset = queryset_map[content_type]
            results_by_model[content_type] = queryset.filter(pk__in=hit_pks)

        all_results = []
        for content_type, hits in results_by_model.items():
            for hit in hits:
                score_key = '%s:%d' % (content_type, hit.pk)
                setattr(hit, 'search_score', scores[score_key])
                all_results.append(hit)
        sorted_results = sorted(
            all_results, key=lambda h: h.search_score, reverse=True)

        return sorted_results


class DashboardMultiTypeSearchBackend(elasticsearch2.Elasticsearch2SearchBackend):
    results_class = DashboardSearchResults
    query_class = DashboardSearchQuery

    def search(self, query_string, model_or_queryset=None, fields=None, filters=None,
               prefetch_related=None, operator=None, order_by_relevance=True):
        if model_or_queryset:
            return super(DashboardMultiTypeSearchBackend, self).search(
                query_string, model_or_queryset, fields, filters, prefetch_related,
                operator, order_by_relevance)
        else:
            # Here comes the fun, search by all models
            search_query = self.query_class(
                None, query_string, fields=fields, operator=operator,
                order_by_relevance=order_by_relevance
            )
            return self.results_class(self, search_query)

SearchBackend = DashboardMultiTypeSearchBackend
