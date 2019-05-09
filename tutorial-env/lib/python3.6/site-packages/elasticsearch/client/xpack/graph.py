from elasticsearch.client.utils import NamespacedClient, query_params, _make_path

class GraphClient(NamespacedClient):
    @query_params('routing', 'timeout')
    def explore(self, index=None, doc_type=None, body=None, params=None):
        """
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/graph-explore-api.html>`_

        :arg index: A comma-separated list of index names to search; use `_all`
            or empty string to perform the operation on all indices
        :arg doc_type: A comma-separated list of document types to search; leave
            empty to perform the operation on all types
        :arg body: Graph Query DSL
        :arg routing: Specific routing value
        :arg timeout: Explicit operation timeout
        """
        return self.transport.perform_request('GET', _make_path(index, doc_type,
            '_xpack', 'graph', '_explore'), params=params, body=body)
